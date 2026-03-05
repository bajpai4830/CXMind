from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Interaction
from app.schemas import AnalyticsSummary
from app.customer_segmentation import segment_customers
from app.cx_forecast import predict_cx_risk
from app.customer_risk import calculate_customer_risk

router = APIRouter(prefix="/api/v1", tags=["analytics"])


# ----------------------------------------------------
# SUMMARY ANALYTICS
# ----------------------------------------------------

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


# ----------------------------------------------------
# TOP COMPLAINT TOPICS
# ----------------------------------------------------

@router.get("/analytics/top-topics")
def top_topics(db: Session = Depends(get_db)):

    rows = (
        db.query(
            Interaction.topic,
            func.count(Interaction.id).label("count")
        )
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


# ----------------------------------------------------
# SENTIMENT TREND OVER TIME
# ----------------------------------------------------

@router.get("/analytics/sentiment-trend")
def sentiment_trend(db: Session = Depends(get_db)):

    rows = (
        db.query(
            func.date(Interaction.created_at).label("date"),
            func.avg(Interaction.sentiment_compound).label("avg_sentiment"),
            func.count(Interaction.id).label("count")
        )
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
def get_customer_risk(customer_id: str, db: Session = Depends(get_db)):

    interactions = (
        db.query(Interaction)
        .filter(Interaction.customer_id == customer_id)
        .order_by(Interaction.created_at.desc())
        .all()
    )

    if not interactions:
        return {
            "customer_id": customer_id,
            "total_interactions": 0,
            "risk_score": 0,
            "risk_level": "no_data"
        }

    risk = calculate_customer_risk(interactions)

    return {
        "customer_id": customer_id,
        "total_interactions": len(interactions),
        "risk_score": risk["risk_score"],
        "risk_level": risk["risk_level"],
    }


# ----------------------------------------------------
# HIGH RISK CUSTOMERS LIST
# ----------------------------------------------------

@router.get("/analytics/high-risk-customers")
def high_risk_customers(db: Session = Depends(get_db)):

    customers = db.query(Interaction.customer_id).distinct().all()

    results = []

    for (cid,) in customers:

        interactions = (
            db.query(Interaction)
            .filter(Interaction.customer_id == cid)
            .all()
        )

        risk = calculate_customer_risk(interactions)

        if risk["risk_level"] == "high_risk":
            results.append({
                "customer_id": cid,
                "risk_score": risk["risk_score"],
                "total_interactions": len(interactions)
            })

@router.get("/analytics/cx-forecast")
def cx_forecast(db: Session = Depends(get_db)):
    return predict_cx_risk(db)

@router.get("/analytics/customer-segments")
def customer_segments(db: Session = Depends(get_db)):
    return segment_customers(db)

@router.get("/analytics/customer-journey")
def customer_journey(customer_id: str, db: Session = Depends(get_db)):

    interactions = (
        db.query(Interaction)
        .filter(Interaction.customer_id == customer_id)
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

    return results