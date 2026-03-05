from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.db import get_db
from app.models import Interaction

router = APIRouter(prefix="/api/v1", tags=["journey"])


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