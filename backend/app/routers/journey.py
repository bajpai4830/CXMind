from fastapi import APIRouter, Depends
from sqlalchemy import asc, case, func
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Interaction, JourneyEvent

router = APIRouter(prefix="/api/v1", tags=["journey"], dependencies=[Depends(get_current_user)])


@router.get("/customer-journey/{customer_id}")
def customer_journey(customer_id: str, db: Session = Depends(get_db)):

    interactions = (
        db.query(Interaction)
        .filter(Interaction.customer_id == customer_id)
        .order_by(asc(Interaction.created_at))
        .all()
    )

    journey = []

    for i in interactions:
        journey.append({
            "time": i.created_at,
            "channel": i.channel,
            "topic": i.topic,
            "sentiment": i.sentiment_label
        })

    return {
        "customer_id": customer_id,
        "steps": journey
    }


@router.get("/journey")
def journey_overview(db: Session = Depends(get_db)):
    rows = (
        db.query(
            JourneyEvent.stage.label("stage"),
            func.count(JourneyEvent.id).label("events"),
            func.sum(case((Interaction.sentiment_label == "negative", 1), else_=0)).label("negative_events"),
            func.avg(Interaction.sentiment_compound).label("avg_sentiment"),
        )
        .join(Interaction, JourneyEvent.interaction_id == Interaction.id, isouter=True)
        .group_by(JourneyEvent.stage)
        .order_by(func.count(JourneyEvent.id).desc())
        .all()
    )

    by_stage = []
    for r in rows:
        events = int(r.events or 0)
        negative_events = int(r.negative_events or 0)
        by_stage.append(
            {
                "stage": r.stage,
                "events": events,
                "negative_events": negative_events,
                "negative_ratio": (negative_events / events) if events else 0.0,
                "avg_sentiment": float(r.avg_sentiment or 0.0),
            }
        )

    friction = sorted(by_stage, key=lambda x: (x["negative_ratio"], x["events"]), reverse=True)[:3]

    return {
        "by_stage": by_stage,
        "top_friction_stages": friction,
    }
