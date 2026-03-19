from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, enabled: bool = True) -> None:
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        response: Response = await call_next(request)
        if not self.enabled:
            return response

        # Minimal security headers: prod-grade full suite nahi, but basics cover ho jaate hain.
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
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
