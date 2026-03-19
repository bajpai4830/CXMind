from __future__ import annotations

import math
from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import CxRiskPrediction, Interaction


@dataclass(frozen=True)
class RiskScore:
    risk_score: float  # [0, 1]
    risk_level: str  # low|medium|high|unknown
    model_name: str
    features: dict


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def compute_customer_features(db: Session, customer_id: str) -> dict:
    # Features are deliberately simple and explainable; this can be replaced by a trained model.
    total = int(
        db.query(func.count(Interaction.id))
        .filter(Interaction.customer_id == customer_id)
        .scalar()
        or 0
    )

    if total == 0:
        return {"total_interactions": 0}

    negative = int(
        db.query(func.count(Interaction.id))
        .filter(Interaction.customer_id == customer_id)
        .filter(Interaction.sentiment_label == "negative")
        .scalar()
        or 0
    )

    avg_sent = float(
        db.query(func.avg(Interaction.sentiment_compound))
        .filter(Interaction.customer_id == customer_id)
        .scalar()
        or 0.0
    )

    # Topic counts for a few high-signal issues.
    def topic_count(topic: str) -> int:
        return int(
            db.query(func.count(Interaction.id))
            .filter(Interaction.customer_id == customer_id)
            .filter(Interaction.topic == topic)
            .scalar()
            or 0
        )

    return {
        "total_interactions": total,
        "negative_count": negative,
        "negative_ratio": (negative / total) if total else 0.0,
        "avg_sentiment": avg_sent,
        "refund_count": topic_count("refund_request"),
        "payment_count": topic_count("payment_problem"),
        "support_delay_count": topic_count("support_delay"),
        "delivery_issue_count": topic_count("delivery_issue"),
        "technical_bug_count": topic_count("technical_bug"),
    }


def predict_risk(features: dict) -> RiskScore:
    total = int(features.get("total_interactions") or 0)
    if total <= 0:
        return RiskScore(risk_score=0.0, risk_level="unknown", model_name="heuristic:v1", features=features)

    # Weighted, monotonic risk score (explainable).
    x = 0.0
    x += 2.2 * float(features.get("negative_ratio") or 0.0)
    x += 0.8 * float(features.get("refund_count") or 0.0) / max(1.0, total)
    x += 0.6 * float(features.get("payment_count") or 0.0) / max(1.0, total)
    x += 0.5 * float(features.get("support_delay_count") or 0.0) / max(1.0, total)
    x += 0.4 * float(features.get("technical_bug_count") or 0.0) / max(1.0, total)
    x += 0.25 * float(features.get("delivery_issue_count") or 0.0) / max(1.0, total)
    x += -0.8 * float(features.get("avg_sentiment") or 0.0)

    score = float(max(0.0, min(1.0, _sigmoid(2.2 * x) )))

    if score >= 0.75:
        level = "high"
    elif score >= 0.45:
        level = "medium"
    else:
        level = "low"

    return RiskScore(risk_score=score, risk_level=level, model_name="heuristic:v1", features=features)


def compute_and_store(db: Session, customer_id: str) -> RiskScore:
    features = compute_customer_features(db, customer_id)
    risk = predict_risk(features)
    row = CxRiskPrediction(
        customer_id=customer_id,
        model_name=risk.model_name,
        risk_score=risk.risk_score,
        risk_level=risk.risk_level,
        features=risk.features,
    )
    db.add(row)
    db.flush()
    return risk

