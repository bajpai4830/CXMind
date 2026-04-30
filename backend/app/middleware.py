from __future__ import annotations

import hmac
import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


class CsrfMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        enabled: bool = True,
        auth_cookie_name: str = "cxmind_token",
        token_cookie_name: str = "cxmind_csrf",
        token_header_name: str = "X-CSRF-Token",
    ) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.auth_cookie_name = auth_cookie_name
        self.token_cookie_name = token_cookie_name
        self.token_header_name = token_header_name

        self._safe_methods = {"GET", "HEAD", "OPTIONS", "TRACE"}
        self._exempt_paths = {"/api/v1/auth/login", "/api/v1/auth/register"}

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if not self.enabled:
            return await call_next(request)

        if request.method in self._safe_methods:
            return await call_next(request)

        if request.url.path in self._exempt_paths:
            return await call_next(request)

        # If the request is authenticated via an Authorization header, it is not subject to CSRF.
        auth_header = request.headers.get("authorization") or ""
        if auth_header.startswith("Bearer "):
            return await call_next(request)

        # Only enforce CSRF when cookie-based auth is in use.
        if not request.cookies.get(self.auth_cookie_name):
            return await call_next(request)

        csrf_cookie = request.cookies.get(self.token_cookie_name) or ""
        csrf_header = request.headers.get(self.token_header_name) or ""
        if not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie, csrf_header):
            return JSONResponse({"detail": "CSRF token missing or invalid"}, status_code=403)

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, enabled: bool = True, headers: dict[str, str] | None = None) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.headers = dict(headers or {})

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        response: Response = await call_next(request)
        if not self.enabled:
            return response

        for header_name, header_value in self.headers.items():
            if header_value:
                response.headers.setdefault(header_name, header_value)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        enabled: bool,
        per_minute: int,
        auth_per_minute: int,
    ) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.per_minute = max(1, int(per_minute))
        self.auth_per_minute = max(1, int(auth_per_minute))
        self.window_seconds = 60.0

        self._hits: dict[str, Deque[float]] = defaultdict(deque)
        self._request_count = 0

    def _client_key(self, request: Request) -> str:
        # Simple key = client IP. Multi-proxy setups me X-Forwarded-For handle karna padega.
        host = request.client.host if request.client else "unknown"
        return host

    def _limit_for(self, path: str) -> int:
        # Auth endpoints pe stricter limit, warna general limit.
        if path.startswith("/api/v1/auth/"):
            return self.auth_per_minute
        return self.per_minute

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if not self.enabled:
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        if path in {"/health"}:
            return await call_next(request)

        key = self._client_key(request)
        now = time.time()
        limit = self._limit_for(path)

        # Periodic garbage collection of empty deques to prevent memory leaks linearly growing with unique IPs
        self._request_count += 1
        if self._request_count % 1000 == 0:
            empty_keys = []
            for k, hits in list(self._hits.items()):
                while hits and now - hits[0] > self.window_seconds:
                    hits.popleft()
                if not hits:
                    empty_keys.append(k)
            for k in empty_keys:
                if k in self._hits and not self._hits[k]:
                    del self._hits[k]

        q = self._hits[key]
        while q and now - q[0] > self.window_seconds:
            q.popleft()

        if len(q) >= limit:
            retry_after = int(max(1.0, self.window_seconds - (now - q[0]))) if q else int(self.window_seconds)
            return JSONResponse(
                {"detail": "Rate limit exceeded"},
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )

        q.append(now)
        return await call_next(request)
