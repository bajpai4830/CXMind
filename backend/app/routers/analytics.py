from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.routers.analytics_export_routes import register_export_routes
from app.routers.analytics_insight_routes import register_insight_routes
from app.routers.analytics_summary_routes import analytics_summary, register_summary_routes, top_topics

router = APIRouter(prefix="/api/v1", tags=["analytics"], dependencies=[Depends(get_current_user)])

register_summary_routes(router)
register_insight_routes(router)
register_export_routes(router)

__all__ = ["analytics_summary", "router", "top_topics"]
