"""Bulk ingestion routes for JSON and CSV interaction imports."""

import csv
import io
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, AuthUser
from app.models import Interaction, _utcnow
from app.schemas import InteractionCreate
from app.services import customer_service, processing_service
import datetime as dt

router = APIRouter(prefix="/api/v1/ingestion", tags=["ingestion"], dependencies=[Depends(get_current_user)])


@router.post("/bulk-json")
def ingest_bulk_json(payload: list[InteractionCreate], db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    """Ingests a list of raw interaction payloads.

    Args:
        payload: Raw JSON interaction records submitted by a client.
        db: Database session used to persist interactions.
        user: Authenticated user context that supplies the tenant organization.

    Returns:
        dict[str, int]: The number of records inserted.
    """

    inserted_count = 0
    batch_time = _utcnow()
    for i, item in enumerate(payload):
        try:
            with db.begin_nested():
                customer_id = item.customer_id.strip() if item.customer_id else None
                if customer_id:
                    customer_service.ensure_customer(db, customer_id, user.org_id)
                    
                if not item.timestamp:
                    occurred_at = _utcnow()
                else:
                    occurred_at = item.timestamp
                    if occurred_at.tzinfo is None:
                        occurred_at = occurred_at.replace(tzinfo=dt.timezone.utc)

                created_at = batch_time - dt.timedelta(microseconds=i)

                interaction = Interaction(
                    org_id=user.org_id,
                    customer_id=customer_id,
                    channel=item.channel,
                    text=item.text,
                    sentiment_compound=0.0,
                    sentiment_label="neutral",
                    interaction_type=item.interaction_type,
                    session_id=item.session_id,
                    occurred_at=occurred_at,
                    created_at=created_at,
                )
                db.add(interaction)
                db.flush()
                processing_service.enrich_interaction(db, interaction)
            inserted_count += 1
        except Exception:
            # Skip invalid item
            continue
        
    db.commit()
    return {"inserted": inserted_count}


@router.post("/upload-csv")
async def ingest_csv(file: UploadFile = File(...), db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    """Ingests a CSV file of interactions for the authenticated organization.

    Args:
        file: Uploaded CSV file containing interaction records.
        db: Database session used to persist interactions.
        user: Authenticated user context that supplies the tenant organization.

    Returns:
        dict[str, int]: The number of records inserted from the CSV file.

    Raises:
        HTTPException: If the uploaded file is not a UTF-8 encoded CSV.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    try:
        decoded_csv = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Please upload UTF-8 CSV.")

    reader = csv.DictReader(io.StringIO(decoded_csv))
    required_columns = {"channel", "message"}
    actual_columns = set(reader.fieldnames or [])
    missing_columns = sorted(required_columns - actual_columns)
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid CSV format. Missing required columns: {', '.join(missing_columns)}",
        )

    processed_count = 0
    failed_count = 0
    batch_time = _utcnow()

    for i, row_data in enumerate(reader):
        customer_id = (row_data.get("customer_id") or "").strip()
        channel = (row_data.get("channel") or "").strip()
        text = (row_data.get("message") or "").strip()
        timestamp_str = (row_data.get("timestamp") or row_data.get("occurred_at") or "").strip()

        if not channel or not text:
            failed_count += 1
            continue

        occurred_at = None
        if timestamp_str:
            try:
                parsed = dt.datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=dt.timezone.utc)
                occurred_at = parsed
            except ValueError:
                pass

        # If timestamp missing -> set current time
        if not occurred_at:
            occurred_at = _utcnow()

        created_at = batch_time - dt.timedelta(microseconds=i)

        try:
            with db.begin_nested():
                if customer_id:
                    customer_service.ensure_customer(db, customer_id, user.org_id)
                interaction = Interaction(
                    org_id=user.org_id,
                    customer_id=customer_id if customer_id else None,
                    channel=channel,
                    text=text,
                    sentiment_compound=0.0,
                    sentiment_label="neutral",
                    occurred_at=occurred_at,
                    created_at=created_at,
                )
                db.add(interaction)
                db.flush()
                processing_service.enrich_interaction(db, interaction)
            processed_count += 1
        except Exception:
            # Keep ingest resilient for real-world files: skip bad rows and continue.
            failed_count += 1
            continue

    db.commit()
    return {"processed": processed_count, "failed": failed_count}
