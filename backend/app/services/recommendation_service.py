from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecommendationItem:
    recommendation: str
    priority: str  # low|medium|high


def recommend(*, topic: str | None, sentiment_label: str | None, stage: str | None, intent: str | None) -> list[RecommendationItem]:
    topic = (topic or "").lower()
    sentiment_label = (sentiment_label or "").lower()
    stage = (stage or "").lower()
    intent = (intent or "").lower()

    recs: list[RecommendationItem] = []

    def add(text: str, priority: str = "medium") -> None:
        recs.append(RecommendationItem(recommendation=text, priority=priority))

    if sentiment_label == "negative" and stage in {"checkout"}:
        add("Audit checkout friction: payment failures, form errors, and latency; add retries and clearer error messaging.", "high")

    if topic == "payment_problem" and sentiment_label == "negative":
        add("Optimize payment gateway reliability/latency; implement idempotent retries and proactive failure alerts.", "high")

    if topic == "support_delay":
        add("Reduce support response times: monitor SLA, improve staffing/triage, and expand self-serve help content.", "high")

    if topic == "delivery_issue":
        add("Improve delivery ETA accuracy and proactive notifications; review carrier SLAs and exception handling.", "medium")

    if topic == "technical_bug":
        add("Prioritize bug fixes: add crash monitoring, release health checks, and rollback mechanisms.", "high")

    if intent == "refund_request":
        add("Streamline refunds: clarify policy, shorten refund cycles, and analyze root causes driving refund requests.", "high")

    if not recs and sentiment_label == "negative":
        add("Investigate recurring complaint drivers and add a closed-loop process to validate improvements.", "medium")

    if sentiment_label == "positive" and topic == "positive_feedback":
        add("Leverage positive feedback: request referrals/reviews and reinforce the journey steps that delight customers.", "low")

    return recs

