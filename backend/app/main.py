from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager

from app import db
from app.scheduler import start_scheduler, shutdown_scheduler
from app.middleware import CsrfMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware
from app.routers.compat import router as compat_router
from app.routers import admin
from app.routers.analytics import router as analytics_router
from app.routers.auth import router as auth_router
from app.routers.feedback import router as feedback_router
from app.routers.health import router as health_router
from app.routers.journey import router as journey_router
from app.routers.interactions import router as interactions_router
from app.routers.ingestion import router as ingestion_router
from app.settings import reset_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    shutdown_scheduler()

def create_app() -> FastAPI:
    settings = reset_settings()
    engine = db.init_engine(settings.database_url)

    app = FastAPI(title="CXMind API", version="0.1.0", lifespan=lifespan)

    from app.routers import auth
    app.state.limiter = auth.limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    app.add_middleware(
        CsrfMiddleware,
        enabled=settings.csrf_enabled,
        token_cookie_name=settings.csrf_cookie_name,
        token_header_name=settings.csrf_header_name,
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
    app.include_router(ingestion_router)
    return app


app = create_app()

