from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
import uuid
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthUser, get_current_user
from app.models import AuditLog
from app.schemas import TokenResponse, UserLogin, UserOut, UserRegister
from app.settings import get_settings
from app.services import auth_service

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _login_rate_limit() -> str:
    return get_settings().rate_limit_login


def _rate_limit_exempt() -> bool:
    return not get_settings().rate_limit_enabled


@router.post("/register", response_model=UserOut)
def register(payload: UserRegister, db: Session = Depends(get_db)) -> UserOut:
    settings = get_settings()
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
def login(request: Request, payload: UserLogin, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    settings = get_settings()
    user = auth_service.authenticate(db, email=payload.email, password=payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if payload.requested_role and user.role != payload.requested_role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Unauthorized: You do not have the '{payload.requested_role}' role.")

    audit = AuditLog(
        actor_id=user.id, 
        action="login", 
        target_id=user.id,
        target_type="user",
        metadata_={"role": user.role},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit)
    db.commit()

    token, ttl = auth_service.encode_access_token(user_id=user.id, role=user.role, token_version=user.token_version)
    
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=ttl,
        httponly=True,
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
    )
    
    # Generate CSRF token for Double-Submit Cookie pattern
    csrf_token = str(uuid.uuid4())
    # TRADE-OFF COMMENT: We use a Double-Submit Cookie pattern for CSRF protection. 
    # The CSRF cookie is NOT HttpOnly so the JS frontend can read it and send it back as a header.
    # WARNING: This means if there is an XSS vulnerability, an attacker can read this cookie 
    # and forge requests. A stronger pattern would be a Synchronizer Token stored server-side.
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        max_age=ttl,
        httponly=False,  # Needs to be readable by JS
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
    )

    return TokenResponse(access_token=token, expires_in=ttl)


@router.post("/logout")
def logout(response: Response):
    settings = get_settings()
    response.delete_cookie(settings.auth_cookie_name)
    response.delete_cookie(settings.csrf_cookie_name)
    return {"detail": "Logged out"}


@router.get("/me")
def me(user: AuthUser = Depends(get_current_user)) -> dict:
    return {"id": user.id, "email": user.email, "role": user.role}
