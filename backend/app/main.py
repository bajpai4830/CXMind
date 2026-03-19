from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import Base, engine
from app.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from app.routers.compat import router as compat_router
from app.routers import admin
from app.routers.analytics import router as analytics_router
from app.routers.auth import router as auth_router
from app.routers.feedback import router as feedback_router
from app.routers.health import router as health_router
from app.routers.journey import router as journey_router
from app.routers.interactions import router as interactions_router
from app.settings import settings


def create_app() -> FastAPI:
    app = FastAPI(title="CXMind API", version="0.1.0")

    # SQLite-only convenience (dev/tests). Postgres ke liye Alembic migrations use karo.
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        # Local dev me explicit origins best hain; empty aaya toh fallback "*" rahega.
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        RateLimitMiddleware,
        enabled=settings.rate_limit_enabled,
        per_minute=settings.rate_limit_per_minute,
        auth_per_minute=settings.rate_limit_auth_per_minute,
    )
    app.add_middleware(SecurityHeadersMiddleware, enabled=settings.security_headers_enabled)

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(interactions_router)
    app.include_router(feedback_router)
    app.include_router(analytics_router)
    app.include_router(admin.router)
    app.include_router(journey_router)
    app.include_router(compat_router)
    return app


app = create_app()

