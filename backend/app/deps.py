from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.services import auth_service
from app.settings import settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@dataclass(frozen=True)
class AuthUser:
    id: int
    email: str
    role: str


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> AuthUser:
    if not settings.auth_enabled:
        # Dev mode shortcut: auth off hai toh admin user treat karo (demo/quickstart ke liye).
        return AuthUser(id=0, email="dev@local", role="admin")

    try:
        claims = auth_service.decode_access_token(token)
        user_id = int(claims.sub)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    row = auth_service.get_user_by_id(db, user_id)
    if row is None or not row.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

    return AuthUser(id=row.id, email=row.email, role=row.role)


def require_role(required_role: str):
    def _dep(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        # Simple RBAC: admin sab kuch kar sakta hai; warna exact role match chahiye.
        if user.role == "admin":
            return user
        if user.role != required_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _dep

