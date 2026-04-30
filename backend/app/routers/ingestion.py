"""Bulk ingestion routes for JSON and CSV interaction imports."""

import csv
import io
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, AuthUser
from app.models import Interaction
from app.services import customer_service, processing_service

router = APIRouter(prefix="/api/v1/ingestion", tags=["ingestion"], dependencies=[Depends(get_current_user)])


@router.post("/bulk-json")
def ingest_bulk_json(payload: list[dict], db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    """Ingests a list of raw interaction payloads.

    Args:
        payload: Raw JSON interaction records submitted by a client.
        db: Database session used to persist interactions.
        user: Authenticated user context that supplies the tenant organization.

    Returns:
        dict[str, int]: The number of records inserted.
    """

    inserted_count = 0
    for item in payload:
        channel = item.get("channel", "bulk_json")
        text = item.get("text")
        if not text:
            continue
            
        customer_id = item.get("customer_id")
        if customer_id:
            customer_service.ensure_customer(db, str(customer_id), user.org_id)
            
        interaction = Interaction(
            org_id=user.org_id,
            customer_id=str(customer_id) if customer_id else None,
            channel=channel,
            text=str(text),
            sentiment_compound=0.0,
            sentiment_label="neutral",
            interaction_type=item.get("interaction_type"),
            session_id=item.get("session_id"),
        )
        db.add(interaction)
        db.flush()
        processing_service.enrich_interaction(db, interaction)
        inserted_count += 1
        
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
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")
        
    content = await file.read()
    try:
        decoded_csv = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Please upload UTF-8 CSV.")
        
    reader = csv.DictReader(io.StringIO(decoded_csv))
    inserted_count = 0
    
    for row_data in reader:
        text = row_data.get("text") or row_data.get("message") or row_data.get("content")
        if not text:
            continue
            
        channel = row_data.get("channel", "csv_upload")
        customer_id = row_data.get("customer_id")
        
        if customer_id:
            customer_service.ensure_customer(db, str(customer_id), user.org_id)
            
        interaction = Interaction(
            org_id=user.org_id,
            customer_id=str(customer_id) if customer_id else None,
            channel=channel,
            text=str(text),
            sentiment_compound=0.0,
            sentiment_label="neutral",
        )
        db.add(interaction)
        db.flush()
        processing_service.enrich_interaction(db, interaction)
        inserted_count += 1
        
    db.commit()
    return {"inserted": inserted_count}
