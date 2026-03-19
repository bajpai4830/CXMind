from __future__ import annotations

from dataclasses import dataclass


JOURNEY_STAGES = [
    "Awareness",
    "Onboarding",
    "Usage",
    "Checkout",
    "Support",
    "Retention",
]


@dataclass(frozen=True)
class JourneyStageScore:
    stage: str
    confidence: float
    method: str  # rules|ml


def map_stage(
    *,
    text: str,
    channel: str | None,
    topic: str | None,
    intent: str | None,
) -> JourneyStageScore:
    t = (text or "").lower()
    topic = (topic or "").lower()
    intent = (intent or "").lower()
    channel = (channel or "").lower()

    def has(words: list[str]) -> bool:
        return any(w in t for w in words)

    # Strong signals first.
    if intent in {"refund_request"} or topic in {"refund_request", "support_delay"}:
        return JourneyStageScore(stage="Support", confidence=0.85, method="rules")

    if intent in {"billing_issue"} or topic in {"payment_problem", "billing_problem"}:
        return JourneyStageScore(stage="Checkout", confidence=0.8, method="rules")

    if intent in {"account_access"} or has(["signup", "sign up", "register", "activation", "activate", "otp", "verify", "verification", "login"]):
        return JourneyStageScore(stage="Onboarding", confidence=0.72, method="rules")

    if intent in {"technical_support"} or topic in {"technical_bug"} or has(["crash", "bug", "error", "freeze", "slow", "lag", "not working"]):
        return JourneyStageScore(stage="Usage", confidence=0.7, method="rules")

    if intent in {"delivery_issue"} or topic in {"delivery_issue"}:
        return JourneyStageScore(stage="Retention", confidence=0.6, method="rules")

    if channel in {"social"} or has(["pricing", "price", "how much", "trial", "considering", "looking for"]):
        return JourneyStageScore(stage="Awareness", confidence=0.55, method="rules")

    # Default: ongoing relationship.
    return JourneyStageScore(stage="Retention", confidence=0.4, method="rules")

