from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, AuthUser
from app.models import Interaction, Recommendation, Customer
from app.schemas import AnalyticsSummary
from app.customer_segmentation import segment_customers
from app.cx_forecast import predict_cx_risk
from app.services import risk_service

router = APIRouter(prefix="/api/v1", tags=["analytics"], dependencies=[Depends(get_current_user)])


# ----------------------------------------------------
# SUMMARY ANALYTICS
# ----------------------------------------------------

@router.get("/analytics/summary", response_model=AnalyticsSummary)
def analytics_summary(db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)) -> AnalyticsSummary:
    total = int(db.query(func.count(Interaction.id)).filter(Interaction.org_id == user.org_id).scalar() or 0)
    avg = float(db.query(func.avg(Interaction.sentiment_compound)).filter(Interaction.org_id == user.org_id).scalar() or 0.0)

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
        .filter(Interaction.org_id == user.org_id)
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


# ----------------------------------------------------
# TOP COMPLAINT TOPICS
# ----------------------------------------------------

@router.get("/analytics/top-topics")
def top_topics(db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    rows = (
        db.query(
            Interaction.topic,
            func.count(Interaction.id).label("count")
        )
        .filter(Interaction.org_id == user.org_id)
        .group_by(Interaction.topic)
        .order_by(func.count(Interaction.id).desc())
        .all()
    )

    return [
        {
            "topic": r.topic,
            "count": int(r.count)
        }
        for r in rows
    ]


@router.get("/analytics/topics")
def topics_alias(db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    return top_topics(db, user)


# ----------------------------------------------------
# SENTIMENT TREND OVER TIME
# ----------------------------------------------------

@router.get("/analytics/sentiment-trend")
def sentiment_trend(db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    rows = (
        db.query(
            func.date(Interaction.created_at).label("date"),
            func.avg(Interaction.sentiment_compound).label("avg_sentiment"),
            func.count(Interaction.id).label("count")
        )
        .filter(Interaction.org_id == user.org_id)
        .group_by(func.date(Interaction.created_at))
        .order_by(func.date(Interaction.created_at))
        .all()
    )

    return [
        {
            "date": str(r.date),
            "avg_sentiment": float(r.avg_sentiment or 0.0),
            "interactions": int(r.count)
        }
        for r in rows
    ]


# ----------------------------------------------------
# CUSTOMER RISK SCORE
# ----------------------------------------------------

@router.get("/analytics/customer-risk/{customer_id}")
def get_customer_risk(customer_id: str, db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id, Customer.org_id == user.org_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    features = risk_service.compute_customer_features(db, customer_id)
    risk = risk_service.predict_risk(features)
    return {
        "customer_id": customer_id,
        "features": features,
        "risk_score": risk.risk_score,
        "risk_level": risk.risk_level,
        "model": risk.model_name,
    }


# ----------------------------------------------------
# HIGH RISK CUSTOMERS LIST
# ----------------------------------------------------

@router.get("/analytics/high-risk-customers")
def high_risk_customers(db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    customers = (
        db.query(Interaction.customer_id)
        .filter(Interaction.customer_id.isnot(None), Interaction.org_id == user.org_id)
        .distinct()
        .all()
    )

    results = []
    for (cid,) in customers:
        if not cid:
            continue
        features = risk_service.compute_customer_features(db, cid)
        risk = risk_service.predict_risk(features)
        if risk.risk_level == "high":
            results.append(
                {
                    "customer_id": cid,
                    "risk_score": risk.risk_score,
                    "risk_level": risk.risk_level,
                    "total_interactions": int(features.get("total_interactions") or 0),
                }
            )

    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results


@router.get("/analytics/cx-risk")
def cx_risk_overview(db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    customers = (
        db.query(Interaction.customer_id)
        .filter(Interaction.customer_id.isnot(None), Interaction.org_id == user.org_id)
        .distinct()
        .all()
    )

    by_level: dict[str, int] = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
    scored: list[dict] = []

    for (cid,) in customers:
        if not cid:
            continue
        features = risk_service.compute_customer_features(db, cid)
        risk = risk_service.predict_risk(features)
        by_level[risk.risk_level] = by_level.get(risk.risk_level, 0) + 1
        scored.append(
            {
                "customer_id": cid,
                "risk_score": risk.risk_score,
                "risk_level": risk.risk_level,
                "total_interactions": int(features.get("total_interactions") or 0),
            }
        )

    scored.sort(key=lambda x: x["risk_score"], reverse=True)
    return {
        "by_level": by_level,
        "top_at_risk": scored[:50],
        "customers_scored": len(scored),
    }

@router.get("/analytics/cx-forecast")
def cx_forecast(db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    return predict_cx_risk(db, user.org_id)

@router.get("/analytics/customer-segments")
def customer_segments(db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    return segment_customers(db, user.org_id)

@router.get("/analytics/customer-journey")
def customer_journey(customer_id: str, db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id, Customer.org_id == user.org_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    interactions = (
        db.query(Interaction)
        .filter(Interaction.customer_id == customer_id, Interaction.org_id == user.org_id)
        .order_by(Interaction.created_at.asc())
        .all()
    )

    journey = []
    for i in interactions:
        journey.append({
            "channel": i.channel,
            "topic": i.topic,
            "sentiment": i.sentiment_label,
            "time": i.created_at
        })

    return journey


@router.get("/analytics/recommendations")
def list_recommendations(limit: int = 50, db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    limit = max(1, min(int(limit), 500))
    # Recommendations don't explicitly have org_id right now in models.py,
    # but they map to interactions! Or we can join interactions.
    rows = (
        db.query(Recommendation)
        .join(Interaction, Recommendation.interaction_id == Interaction.id)
        .filter(Interaction.org_id == user.org_id)
        .order_by(Recommendation.created_at.desc(), Recommendation.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "customer_id": r.customer_id,
            "interaction_id": r.interaction_id,
            "stage": r.stage,
            "topic": r.topic,
            "priority": r.priority,
            "status": r.status,
            "recommendation": r.recommendation,
            "created_at": r.created_at,
        }
        for r in rows
    ]


def _stream_csv(rows, header: list[str], row_fn):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    yield buf.getvalue()
    buf.seek(0)
    buf.truncate(0)

    for r in rows:
        w.writerow(row_fn(r))
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate(0)


@router.get("/analytics/export/interactions.csv")
def export_interactions_csv(limit: int = 1000, customer_id: str | None = None, db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    limit = max(1, min(int(limit), 10000))

    q = db.query(Interaction).filter(Interaction.org_id == user.org_id).order_by(Interaction.created_at.desc(), Interaction.id.desc())
    if customer_id:
        q = q.filter(Interaction.customer_id == customer_id)
    rows = q.limit(limit).all()

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
            lambda r: [
                r.id,
                r.customer_id,
                r.channel,
                getattr(r, "interaction_type", None),
                getattr(r, "session_id", None),
                getattr(r, "occurred_at", None),
                r.sentiment_label,
                r.sentiment_compound,
                r.topic,
                r.text,
                r.created_at,
            ],
        ),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=interactions.csv"},
    )


@router.get("/analytics/export/recommendations.csv")
def export_recommendations_csv(limit: int = 1000, db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    limit = max(1, min(int(limit), 10000))
    rows = (
        db.query(Recommendation)
        .join(Interaction, Recommendation.interaction_id == Interaction.id)
        .filter(Interaction.org_id == user.org_id)
        .order_by(Recommendation.created_at.desc(), Recommendation.id.desc())
        .limit(limit)
        .all()
    )

    header = ["id", "customer_id", "interaction_id", "stage", "topic", "priority", "status", "recommendation", "created_at"]

    return StreamingResponse(
        _stream_csv(
            rows,
            header,
            lambda r: [
                r.id,
                r.customer_id,
                r.interaction_id,
                r.stage,
                r.topic,
                r.priority,
                r.status,
                r.recommendation,
                r.created_at,
            ],
        ),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=recommendations.csv"},
    )
