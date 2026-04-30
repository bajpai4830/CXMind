from __future__ import annotations

import csv
import io
from collections.abc import Iterable

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthUser, get_current_user
from app.models import Interaction, Recommendation


def _stream_csv(rows: Iterable[object], header: list[str], row_factory):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    yield buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)

    for row in rows:
        writer.writerow(row_factory(row))
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)


def export_interactions_csv(
    limit: int = 1000,
    customer_id: str | None = None,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    safe_limit = max(1, min(int(limit), 10000))
    query = db.query(Interaction).filter(Interaction.org_id == user.org_id).order_by(Interaction.created_at.desc(), Interaction.id.desc())
    if customer_id:
        query = query.filter(Interaction.customer_id == customer_id)

    rows = query.limit(safe_limit).all()
    header = [
        "id",
        "customer_id",
        "channel",
        "interaction_type",
        "session_id",
        "occurred_at",
        "sentiment_label",
        "sentiment_compound",
        "topic",
        "text",
        "created_at",
    ]

    return StreamingResponse(
        _stream_csv(
            rows,
            header,
            lambda row: [
                row.id,
                row.customer_id,
                row.channel,
                getattr(row, "interaction_type", None),
                getattr(row, "session_id", None),
                getattr(row, "occurred_at", None),
                row.sentiment_label,
                row.sentiment_compound,
                row.topic,
                row.text,
                row.created_at,
            ],
        ),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=interactions.csv"},
    )


def export_recommendations_csv(
    limit: int = 1000,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    safe_limit = max(1, min(int(limit), 10000))
    rows = (
        db.query(Recommendation)
        .join(Interaction, Recommendation.interaction_id == Interaction.id)
        .filter(Interaction.org_id == user.org_id)
        .order_by(Recommendation.created_at.desc(), Recommendation.id.desc())
        .limit(safe_limit)
        .all()
    )

    return StreamingResponse(
        _stream_csv(
            rows,
            ["id", "customer_id", "interaction_id", "stage", "topic", "priority", "status", "recommendation", "created_at"],
            lambda row: [
                row.id,
                row.customer_id,
                row.interaction_id,
                row.stage,
                row.topic,
                row.priority,
                row.status,
                row.recommendation,
                row.created_at,
            ],
        ),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=recommendations.csv"},
    )


def register_export_routes(router: APIRouter) -> None:
    router.add_api_route("/analytics/export/interactions.csv", export_interactions_csv, methods=["GET"])
    router.add_api_route("/analytics/export/recommendations.csv", export_recommendations_csv, methods=["GET"])
