from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Interaction
from app.schemas import InteractionCreate, InteractionOut
from app.sentiment import score_text
from app.topic_normalizer import normalize_topic
from app.topic_keywords import keyword_topic
from app.topic_cleaner import clean_topic
from app.topic_clustering import predict_topic, get_topic_label

router = APIRouter(prefix="/api/v1", tags=["interactions"])


@router.post("/interactions", response_model=InteractionOut)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db)) -> InteractionOut:

    s = score_text(payload.text)

    # First try keyword detection
    topic = keyword_topic(payload.text)

    if topic is None:
        # fallback to BERTopic
        topic_id = predict_topic(payload.text)
        raw_topic = get_topic_label(topic_id)

        topic = clean_topic(raw_topic, payload.text, s.label)
        topic = normalize_topic(topic)

    row = Interaction(
        customer_id=payload.customer_id,
        channel=payload.channel,
        text=payload.text,
        sentiment_compound=s.compound,
        sentiment_label=s.label,
        topic=topic
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return row


@router.get("/interactions", response_model=list[InteractionOut])
def list_interactions(limit: int = 50, db: Session = Depends(get_db)) -> list[InteractionOut]:

    limit = max(1, min(int(limit), 500))

    return (
        db.query(Interaction)
        .order_by(Interaction.created_at.desc(), Interaction.id.desc())
        .limit(limit)
        .all()
    )