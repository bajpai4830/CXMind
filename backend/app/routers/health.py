from __future__ import annotations

import datetime as dt

from fastapi import APIRouter
from sqlalchemy import text

from app.db import engine
from app.schemas import HealthResponse
from app.settings import settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(details: bool = False) -> HealthResponse:
    if not details:
        return HealthResponse()

    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1"))
        db_ok = True
    except Exception:
        db_ok = False

    db_kind = "sqlite" if settings.database_url.startswith("sqlite") else "postgres"

    return HealthResponse(
        status="ok" if db_ok else "degraded",
        db_ok=db_ok,
        db=db_kind,
        auth_enabled=settings.auth_enabled,
        time_utc=dt.datetime.now(dt.timezone.utc),
    )
