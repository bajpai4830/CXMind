from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Interaction
from app.schemas import AnalyticsSummary

router = APIRouter(prefix="/api/v1", tags=["analytics"])


@router.get("/analytics/summary", response_model=AnalyticsSummary)
def analytics_summary(db: Session = Depends(get_db)) -> AnalyticsSummary:
    total = int(db.query(func.count(Interaction.id)).scalar() or 0)
    avg = float(db.query(func.avg(Interaction.sentiment_compound)).scalar() or 0.0)

    by_channel_rows = (
        db.query(
            Interaction.channel.label("channel"),
            func.count(Interaction.id).label("count"),
            func.avg(Interaction.sentiment_compound).label("avg_sentiment_compound"),
        )
        .group_by(Interaction.channel)
        .order_by(func.count(Interaction.id).desc())
        .all()
    )
    by_channel = [
        {
            "channel": r.channel,
            "count": int(r.count),
            "avg_sentiment_compound": float(r.avg_sentiment_compound or 0.0),
        }
        for r in by_channel_rows
    ]

    by_label_rows = (
        db.query(
            Interaction.sentiment_label.label("label"),
            func.count(Interaction.id).label("count"),
        )
        .group_by(Interaction.sentiment_label)
        .order_by(func.count(Interaction.id).desc())
        .all()
    )
    by_label = [{"label": r.label, "count": int(r.count)} for r in by_label_rows]

    return AnalyticsSummary(
        total_interactions=total,
        avg_sentiment_compound=avg,
        by_channel=by_channel,
        by_label=by_label,
    )

