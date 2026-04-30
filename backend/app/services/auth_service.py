from __future__ import annotations

import base64
import datetime as dt
import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import Organization, User


PBKDF2_ALG = "sha256"
PBKDF2_ITERATIONS = 260_000
SALT_BYTES = 16


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    s = data.encode("ascii")
    s += b"=" * ((4 - (len(s) % 4)) % 4)
    return base64.urlsafe_b64decode(s)


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def hash_password(password: str) -> str:
    if not isinstance(password, str) or len(password) < 8:
        raise ValueError("password too short")

    salt = secrets.token_bytes(SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(PBKDF2_ALG, password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_{PBKDF2_ALG}${PBKDF2_ITERATIONS}${_b64url_encode(salt)}${_b64url_encode(dk)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, iters_s, salt_b64, hash_b64 = (password_hash or "").split("$", 3)
        if not scheme.startswith("pbkdf2_"):
            return False
        alg = scheme.split("_", 1)[1]
        iters = int(iters_s)
        salt = _b64url_decode(salt_b64)
        expected = _b64url_decode(hash_b64)
        dk = hashlib.pbkdf2_hmac(alg, password.encode("utf-8"), salt, iters)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


@dataclass(frozen=True)
class JwtClaims:
    sub: str
    role: str
    exp: int
    iat: int
    tv: int | None = None
    iss: str | None = None


def _jwt_secret() -> str:
    # Required in production. For local dev, a default is fine.
    return (os.environ.get("CXMIND_JWT_SECRET") or "dev-secret-change-me").strip()


def _jwt_issuer() -> str:
    return (os.environ.get("CXMIND_JWT_ISSUER") or "cxmind").strip()


def _jwt_ttl_seconds() -> int:
    raw = os.environ.get("CXMIND_JWT_TTL_SECONDS") or ""
    try:
        v = int(raw)
        return max(60, min(v, 60 * 60 * 24))
    except Exception:
        return 60 * 60  # 1 hour


def encode_access_token(*, user_id: int, role: str, token_version: int) -> tuple[str, int]:
    now = int(dt.datetime.now(dt.timezone.utc).timestamp())
    ttl = _jwt_ttl_seconds()
    payload = {
        "sub": str(user_id),
        "role": role,
        "tv": token_version,
        "iat": now,
        "exp": now + ttl,
        "iss": _jwt_issuer(),
        "jti": secrets.token_urlsafe(16),
        "typ": "access",
    }

    header = {"alg": "HS256", "typ": "JWT"}

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    sig = hmac.new(_jwt_secret().encode("utf-8"), signing_input, hashlib.sha256).digest()
    token = f"{header_b64}.{payload_b64}.{_b64url_encode(sig)}"
    return token, ttl


def decode_access_token(token: str) -> JwtClaims:
    try:
        header_b64, payload_b64, sig_b64 = token.split(".", 2)
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        sig = _b64url_decode(sig_b64)
        expected = hmac.new(_jwt_secret().encode("utf-8"), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            raise ValueError("bad signature")

        header = json.loads(_b64url_decode(header_b64).decode("utf-8"))
        if header.get("alg") != "HS256":
            raise ValueError("unsupported alg")

        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        now = int(dt.datetime.now(dt.timezone.utc).timestamp())
        exp = int(payload.get("exp") or 0)
        if exp and now >= exp:
            raise ValueError("token expired")

        iss = payload.get("iss")
        if iss and iss != _jwt_issuer():
            raise ValueError("bad issuer")

        return JwtClaims(
            sub=str(payload.get("sub") or ""),
            role=str(payload.get("role") or "analyst"),
            exp=exp,
            iat=int(payload.get("iat") or 0),
            tv=int(payload.get("tv")) if payload.get("tv") is not None else None,
            iss=str(iss) if iss is not None else None,
        )
    except Exception as e:
        raise ValueError("invalid token") from e


def get_user_by_email(db: Session, email: str) -> User | None:
    email = normalize_email(email)
    if not email:
        return None
    return db.query(User).filter(User.email == email).one_or_none()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).one_or_none()


def create_user(db: Session, *, email: str, password: str, role: str) -> User:
    email = normalize_email(email)
    if not email or "@" not in email:
        raise ValueError("invalid email")

    if get_user_by_email(db, email) is not None:
        raise ValueError("email already registered")

    org_name = f"{email.split('@', 1)[0]}'s Workspace"
    organization = Organization(name=org_name)
    db.add(organization)
    db.flush()

    row = User(
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
        token_version=1,
        org_id=organization.id,
    )
    db.add(row)
    db.flush()
    return row


def authenticate(db: Session, *, email: str, password: str) -> User | None:
    row = get_user_by_email(db, email)
    if row is None:
        return None
    if not row.is_active:
        return None
    if not verify_password(password, row.password_hash):
        return None
    return row
