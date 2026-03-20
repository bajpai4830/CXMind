from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, AuthUser
from app.models import Interaction
from app.schemas import InteractionCreate, InteractionLogCreate, InteractionOut
from app.services import customer_service, processing_service

router = APIRouter(prefix="/api/v1", tags=["interactions"], dependencies=[Depends(get_current_user)])


def _create_interaction(payload: InteractionLogCreate, db: Session, org_id: int) -> Interaction:
    customer_id = payload.customer_id.strip() if payload.customer_id else None
    if customer_id:
        customer_service.ensure_customer(db, customer_id, org_id)

    row = Interaction(
        org_id=org_id,
        customer_id=customer_id,
        channel=payload.channel,
        text=payload.text,
        interaction_type=payload.interaction_type,
        session_id=payload.session_id,
        occurred_at=payload.timestamp,
        metadata_=payload.metadata,
        raw_payload=payload.raw_payload,
        sentiment_compound=0.0,
        sentiment_label="neutral",
        topic=None,
    )
    db.add(row)
    db.flush()  # allocate PK for result tables

    processing_service.enrich_interaction(db, row)
    return row


@router.post("/interactions", response_model=InteractionOut)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)) -> InteractionOut:
    # Backward-compatible ingest endpoint (MVP).
    row = _create_interaction(
        InteractionLogCreate(
            customer_id=payload.customer_id,
            channel=payload.channel,
            text=payload.text,
            interaction_type=payload.interaction_type,
            session_id=payload.session_id,
            timestamp=payload.timestamp,
            metadata=payload.metadata,
        ),
        db,
        user.org_id,
    )
    db.commit()
    db.refresh(row)
    return row


@router.post("/interactions/log", response_model=InteractionOut)
def log_interaction(payload: InteractionLogCreate, db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)) -> InteractionOut:
    row = _create_interaction(payload, db, user.org_id)
    db.commit()
    db.refresh(row)
    return row


@router.get("/interactions", response_model=list[InteractionOut])
def list_interactions(limit: int = 50, db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)) -> list[InteractionOut]:

    limit = max(1, min(int(limit), 500))

    return (
        db.query(Interaction)
        .filter(Interaction.org_id == user.org_id)
        .order_by(Interaction.created_at.desc(), Interaction.id.desc())
        .limit(limit)
        .all()
    )
