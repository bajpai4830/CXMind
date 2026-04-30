from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthUser, get_current_user
from app.models import Feedback, Interaction
from app.routers.analytics import analytics_summary
from app.routers.journey import journey_overview
from app.schemas import (
    AnalyticsSummary,
    FeedbackUploadRequest,
    FeedbackUploadResponse,
    InteractionLogCreate,
    InteractionOut,
)
from app.services import customer_service, processing_service


router = APIRouter(prefix="/api", tags=["compat"], dependencies=[Depends(get_current_user)])


@router.post("/interactions/log", response_model=InteractionOut)
def log_interaction(
    payload: InteractionLogCreate,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
) -> InteractionOut:
    customer_id = payload.customer_id.strip() if payload.customer_id else None
    if customer_id:
        customer_service.ensure_customer(db, customer_id, user.org_id)

    row = Interaction(
        org_id=user.org_id,
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
    db.flush()
    processing_service.enrich_interaction(db, row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/feedback/upload", response_model=FeedbackUploadResponse)
def upload_feedback(
    payload: FeedbackUploadRequest,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
) -> FeedbackUploadResponse:
    inserted = 0
    for item in payload.items:
        customer_id = item.customer_id.strip() if item.customer_id else None
        if customer_id:
            customer_service.ensure_customer(db, customer_id, user.org_id)

        interaction = Interaction(
            org_id=user.org_id,
            customer_id=customer_id,
            channel=item.channel,
            text=item.text,
            interaction_type=item.interaction_type,
            session_id=item.session_id,
            occurred_at=item.timestamp,
            metadata_=item.metadata,
            raw_payload=item.raw_payload,
            sentiment_compound=0.0,
            sentiment_label="neutral",
            topic=None,
        )
        db.add(interaction)
        db.flush()

        db.add(
            Feedback(
                interaction_id=interaction.id,
                rating=item.rating,
                title=item.title,
                source=item.source,
            )
        )
        processing_service.enrich_interaction(db, interaction)
        inserted += 1

    db.commit()
    return FeedbackUploadResponse(inserted=inserted)


@router.get("/analytics/summary", response_model=AnalyticsSummary)
def analytics_summary_compat(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
) -> AnalyticsSummary:
    return analytics_summary(db, user)


@router.get("/journey")
def journey_overview_compat(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    return journey_overview(db, user)
