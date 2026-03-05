from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Interaction
from app.topic_clustering import train_topic_model

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/retrain-topic-model")
def retrain_topic_model_endpoint(db: Session = Depends(get_db)):

    interactions = db.query(Interaction).all()

    texts = [i.text for i in interactions]

    if len(texts) < 5:
        return {"status": "not enough data", "count": len(texts)}

    train_topic_model(texts)

    return {
        "status": "topic model retrained",
        "samples_used": len(texts)
    }