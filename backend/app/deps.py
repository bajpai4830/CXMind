"""Authentication and authorization dependencies for FastAPI routes."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.services import auth_service
from app.settings import get_settings

http_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthUser:
    """Normalized authenticated user context attached to a request."""

    id: int
    email: str
    role: str
    org_id: int


def _resolve_access_token(
    request: Request,
    auth_cookie_name: str,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    if credentials is not None and credentials.scheme.lower() == "bearer":
        return credentials.credentials

    return request.cookies.get(auth_cookie_name)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(http_bearer_scheme),
    db: Session = Depends(get_db),
) -> AuthUser:
    """Resolves the authenticated user from cookies or a bearer token.

    Args:
        request: The incoming HTTP request.
        credentials: Optional bearer credentials extracted by FastAPI.
        db: Database session used to load the backing user record.

    Returns:
        AuthUser: The normalized authenticated user context.

    Raises:
        HTTPException: If authentication is disabled, missing, invalid, or revoked.
    """
    settings = get_settings()
    if not settings.auth_enabled:
        # Dev mode shortcut: auth off hai toh admin user treat karo (demo/quickstart ke liye).
        return AuthUser(id=0, email="dev@local", role="admin", org_id=1)

    token = _resolve_access_token(request, settings.auth_cookie_name, credentials)

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        claims = auth_service.decode_access_token(token)
        user_id = int(claims.sub)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    row = auth_service.get_user_by_id(db, user_id)
    if row is None or not row.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")
        
    if claims.tv is not None and row.token_version != claims.tv:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked")

    return AuthUser(id=row.id, email=row.email, role=row.role, org_id=row.org_id)


def require_role(required_role: str):
    """Builds a dependency that enforces a required role for a route.

    Args:
        required_role: The role required to access the route.

    Returns:
        Callable[..., AuthUser]: A dependency that validates the current user.
    """

    def role_dependency(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        # Simple RBAC: admin sab kuch kar sakta hai; warna exact role match chahiye.
        if user.role == "admin":
            return user
        if user.role != required_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return role_dependency
