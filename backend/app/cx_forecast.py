from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Interaction


def predict_cx_risk(db: Session):

    recent_negative = (
        db.query(func.count(Interaction.id))
        .filter(Interaction.sentiment_label == "negative")
        .count()
    )

    total = db.query(func.count(Interaction.id)).scalar()

    if total == 0:
        return {"risk": "unknown"}

    ratio = recent_negative / total

    if ratio > 0.5:
        return {
            "risk_level": "high",
            "prediction": "Customer dissatisfaction likely to increase"
        }

    if ratio > 0.3:
        return {
            "risk_level": "medium",
            "prediction": "Potential CX decline detected"
        }

    return {
        "risk_level": "low",
        "prediction": "Customer experience stable"
    }