from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthUser, get_current_user
from app.models import User
from app.schemas import TokenResponse, UserLogin, UserOut, UserRegister
from app.services import auth_service


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(payload: UserRegister, db: Session = Depends(get_db)) -> UserOut:
    from app.settings import settings
    # Match admin_secret to grant admin role
    role = "admin" if payload.admin_secret and payload.admin_secret == settings.admin_secret else "analyst"

    try:
        row = auth_service.create_user(db, email=payload.email, password=payload.password, role=role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    db.commit()
    db.refresh(row)
    return row


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = auth_service.authenticate(db, email=payload.email, password=payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token, ttl = auth_service.encode_access_token(user_id=user.id, role=user.role)
    return TokenResponse(access_token=token, expires_in=ttl)


@router.get("/me")
def me(user: AuthUser = Depends(get_current_user)) -> dict:
    return {"id": user.id, "email": user.email, "role": user.role}

