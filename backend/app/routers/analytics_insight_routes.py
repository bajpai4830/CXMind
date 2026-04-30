from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.customer_segmentation import segment_customers
from app.cx_forecast import predict_cx_risk
from app.db import get_db
from app.deps import AuthUser, get_current_user
from app.models import Customer, Interaction, Recommendation
from app.services import risk_service


def get_customer_risk(
    customer_id: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id, Customer.org_id == user.org_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    features = risk_service.compute_customer_features(db, customer_id, org_id=user.org_id)
    risk = risk_service.predict_risk(features)
    return {
        "customer_id": customer_id,
        "features": features,
        "risk_score": risk.risk_score,
        "risk_level": risk.risk_level,
        "model": risk.model_name,
    }


def high_risk_customers(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    customers = (
        db.query(Interaction.customer_id)
        .filter(Interaction.customer_id.isnot(None), Interaction.org_id == user.org_id)
        .distinct()
        .all()
    )

    results: list[dict[str, object]] = []
    for (customer_id,) in customers:
        if not customer_id:
            continue
        features = risk_service.compute_customer_features(db, customer_id, org_id=user.org_id)
        risk = risk_service.predict_risk(features)
        if risk.risk_level == "high":
            results.append(
                {
                    "customer_id": customer_id,
                    "risk_score": risk.risk_score,
                    "risk_level": risk.risk_level,
                    "total_interactions": int(features.get("total_interactions") or 0),
                }
            )

    results.sort(key=lambda item: item["risk_score"], reverse=True)
    return results


def cx_risk_overview(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    customers = (
        db.query(Interaction.customer_id)
        .filter(Interaction.customer_id.isnot(None), Interaction.org_id == user.org_id)
        .distinct()
        .all()
    )

    by_level: dict[str, int] = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
    scored: list[dict[str, object]] = []

    for (customer_id,) in customers:
        if not customer_id:
            continue
        features = risk_service.compute_customer_features(db, customer_id, org_id=user.org_id)
        risk = risk_service.predict_risk(features)
        by_level[risk.risk_level] = by_level.get(risk.risk_level, 0) + 1
        scored.append(
            {
                "customer_id": customer_id,
                "risk_score": risk.risk_score,
                "risk_level": risk.risk_level,
                "total_interactions": int(features.get("total_interactions") or 0),
            }
        )

    scored.sort(key=lambda item: item["risk_score"], reverse=True)
    return {"by_level": by_level, "top_at_risk": scored[:50], "customers_scored": len(scored)}


def cx_forecast(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    return predict_cx_risk(db, user.org_id)


def customer_segments(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    return segment_customers(db, user.org_id)


def customer_journey(
    customer_id: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id, Customer.org_id == user.org_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    interactions = (
        db.query(Interaction)
        .filter(Interaction.customer_id == customer_id, Interaction.org_id == user.org_id)
        .order_by(Interaction.created_at.asc())
        .all()
    )

    return [
        {
            "channel": interaction.channel,
            "topic": interaction.topic,
            "sentiment": interaction.sentiment_label,
            "time": interaction.created_at,
        }
        for interaction in interactions
    ]


def list_recommendations(
    limit: int = 50,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    safe_limit = max(1, min(int(limit), 500))
    rows = (
        db.query(Recommendation)
        .join(Interaction, Recommendation.interaction_id == Interaction.id)
        .filter(Interaction.org_id == user.org_id)
        .order_by(Recommendation.created_at.desc(), Recommendation.id.desc())
        .limit(safe_limit)
        .all()
    )

    return [
        {
            "id": row.id,
            "customer_id": row.customer_id,
            "interaction_id": row.interaction_id,
            "stage": row.stage,
            "topic": row.topic,
            "priority": row.priority,
            "status": row.status,
            "recommendation": row.recommendation,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def register_insight_routes(router: APIRouter) -> None:
    router.add_api_route("/analytics/customer-risk/{customer_id}", get_customer_risk, methods=["GET"])
    router.add_api_route("/analytics/high-risk-customers", high_risk_customers, methods=["GET"])
    router.add_api_route("/analytics/cx-risk", cx_risk_overview, methods=["GET"])
    router.add_api_route("/analytics/cx-forecast", cx_forecast, methods=["GET"])
    router.add_api_route("/analytics/customer-segments", customer_segments, methods=["GET"])
    router.add_api_route("/analytics/customer-journey", customer_journey, methods=["GET"])
    router.add_api_route("/analytics/recommendations", list_recommendations, methods=["GET"])
