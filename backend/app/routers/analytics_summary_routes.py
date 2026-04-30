from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthUser, get_current_user
from app.models import Interaction
from app.schemas import AnalyticsSummary


def analytics_summary(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
) -> AnalyticsSummary:
    total = int(db.query(func.count(Interaction.id)).filter(Interaction.org_id == user.org_id).scalar() or 0)
    average_sentiment = float(
        db.query(func.avg(Interaction.sentiment_compound)).filter(Interaction.org_id == user.org_id).scalar() or 0.0
    )

    by_channel_rows = (
        db.query(
            Interaction.channel.label("channel"),
            func.count(Interaction.id).label("count"),
            func.avg(Interaction.sentiment_compound).label("avg_sentiment_compound"),
        )
        .filter(Interaction.org_id == user.org_id)
        .group_by(Interaction.channel)
        .order_by(func.count(Interaction.id).desc())
        .all()
    )

    by_label_rows = (
        db.query(
            Interaction.sentiment_label.label("label"),
            func.count(Interaction.id).label("count"),
        )
        .filter(Interaction.org_id == user.org_id)
        .group_by(Interaction.sentiment_label)
        .order_by(func.count(Interaction.id).desc())
        .all()
    )

    return AnalyticsSummary(
        total_interactions=total,
        avg_sentiment_compound=average_sentiment,
        by_channel=[
            {
                "channel": row.channel,
                "count": int(row.count),
                "avg_sentiment_compound": float(row.avg_sentiment_compound or 0.0),
            }
            for row in by_channel_rows
        ],
        by_label=[{"label": row.label, "count": int(row.count)} for row in by_label_rows],
    )


def top_topics(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    rows = (
        db.query(Interaction.topic, func.count(Interaction.id).label("count"))
        .filter(Interaction.org_id == user.org_id)
        .group_by(Interaction.topic)
        .order_by(func.count(Interaction.id).desc())
        .all()
    )

    return [{"topic": row.topic, "count": int(row.count)} for row in rows]


def topics_alias(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    return top_topics(db, user)


def sentiment_trend(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    rows = (
        db.query(
            func.date(Interaction.created_at).label("date"),
            func.avg(Interaction.sentiment_compound).label("avg_sentiment"),
            func.count(Interaction.id).label("count"),
        )
        .filter(Interaction.org_id == user.org_id)
        .group_by(func.date(Interaction.created_at))
        .order_by(func.date(Interaction.created_at))
        .all()
    )

    return [
        {
            "date": str(row.date),
            "avg_sentiment": float(row.avg_sentiment or 0.0),
            "interactions": int(row.count),
        }
        for row in rows
    ]


def register_summary_routes(router: APIRouter) -> None:
    router.add_api_route("/analytics/summary", analytics_summary, methods=["GET"], response_model=AnalyticsSummary)
    router.add_api_route("/analytics/top-topics", top_topics, methods=["GET"])
    router.add_api_route("/analytics/topics", topics_alias, methods=["GET"])
    router.add_api_route("/analytics/sentiment-trend", sentiment_trend, methods=["GET"])
