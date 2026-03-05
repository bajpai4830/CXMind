from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import Base, engine
from app.routers import admin
from app.routers.analytics import router as analytics_router
from app.routers.health import router as health_router
from app.routers.journey import router as journey_router
from app.routers.interactions import router as interactions_router
from app.settings import settings


def create_app() -> FastAPI:
    app = FastAPI(title="CXMind API", version="0.1.0")

    # Create tables for the MVP. In production, switch to migrations.
    Base.metadata.create_all(bind=engine)

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(interactions_router)
    app.include_router(analytics_router)
    app.include_router(admin.router)
    app.include_router(journey_router)
    return app


app = create_app()

