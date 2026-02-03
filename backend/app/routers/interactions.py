from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Interaction
from app.schemas import InteractionCreate, InteractionOut
from app.sentiment import score_text

router = APIRouter(prefix="/api/v1", tags=["interactions"])


@router.post("/interactions", response_model=InteractionOut)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db)) -> InteractionOut:
    s = score_text(payload.text)

    row = Interaction(
        customer_id=payload.customer_id,
        channel=payload.channel,
        text=payload.text,
        sentiment_compound=s.compound,
        sentiment_label=s.label,
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

