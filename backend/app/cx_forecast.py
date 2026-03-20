from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Interaction

RISK_THRESHOLDS = [
    (0.5, "high", "Customer dissatisfaction likely to increase"),
    (0.3, "medium", "Potential CX decline detected"),
    (-1.0, "low", "Customer experience stable")
]

def predict_cx_risk(db: Session, org_id: int) -> dict[str, str]:
    recent_negative = (
        db.query(func.count(Interaction.id))
        .filter(Interaction.sentiment_label == "negative", Interaction.org_id == org_id)
        .scalar() or 0
    )

    total = db.query(func.count(Interaction.id)).filter(Interaction.org_id == org_id).scalar()
    if not total:
        return {"risk": "unknown"}

    ratio = recent_negative / total

    for threshold, level, prediction in RISK_THRESHOLDS:
        if ratio > threshold:
            return {
                "risk_level": level,
                "prediction": prediction
            }
            
    return {"risk": "unknown"}