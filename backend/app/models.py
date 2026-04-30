"""SQLAlchemy models for CXMind's multi-tenant analytics domain."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class Organization(Base):
    """Represents a tenant workspace that owns users and customer data."""

    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        index=True,
    )


class Customer(Base):
    """Stores a customer profile scoped to an organization."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # External/customer-provided identifier (used across ingests).
    customer_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)

    name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    signup_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    region: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        index=True,
    )


class SystemJob(Base):
    """Tracks long-running or scheduled platform jobs."""

    __tablename__ = "system_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="idle")
    last_run: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    triggered_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class AuditLog(Base):
    """Captures security-sensitive and administrative actions."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(256), nullable=True)
    
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        index=True,
    )


class User(Base):
    """Represents an authenticated platform user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, default=1, index=True)

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)

    role: Mapped[str] = mapped_column(String(32), nullable=False, default="analyst", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        index=True,
    )


class Interaction(Base):
    """Stores a normalized customer interaction for downstream analysis."""

    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    customer_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("customers.customer_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    channel: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Optional high-level fields from various sources.
    interaction_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    occurred_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Sentiment: store a denormalized snapshot for fast analytics.
    sentiment_compound: Mapped[float] = mapped_column(Float, nullable=False)
    sentiment_label: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    topic: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        index=True,
    )


class Feedback(Base):
    """Stores explicit feedback metadata linked to an interaction."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interaction_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("interactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    rating: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        index=True,
    )


class SentimentResult(Base):
    """Persists detailed sentiment model output for an interaction."""

    __tablename__ = "sentiment_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interaction_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("interactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    model_name: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    sentiment: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    compound: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        index=True,
    )


class EmotionResult(Base):
    """Persists detailed emotion model output for an interaction."""

    __tablename__ = "emotion_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interaction_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("interactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    model_name: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    emotion: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        index=True,
    )


class IntentResult(Base):
    """Persists detected intent scores for an interaction."""

    __tablename__ = "intent_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interaction_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("interactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    model_name: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    intent: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        index=True,
    )


class Topic(Base):
    """Catalogs reusable topic labels assigned by topic modeling."""

    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        index=True,
    )


class TopicResult(Base):
    """Stores topic-model output for a single interaction."""

    __tablename__ = "topic_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interaction_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("interactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)

    model_name: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    topic: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        index=True,
    )


class JourneyEvent(Base):
    """Records a derived stage transition in the customer journey."""

    __tablename__ = "journey_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    customer_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    interaction_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("interactions.id", ondelete="SET NULL"), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    stage: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    stage_method: Mapped[str] = mapped_column(String(32), nullable=False, default="rules")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    occurred_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        index=True,
    )


class CxRiskPrediction(Base):
    """Stores customer-level risk predictions generated by analytics jobs."""

    __tablename__ = "cx_risk_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    model_name: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown", index=True)
    features: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    as_of: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        index=True,
    )


class Recommendation(Base):
    """Stores recommended follow-up actions derived from analytics."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    interaction_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("interactions.id", ondelete="SET NULL"), nullable=True)

    stage: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    topic: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="medium", index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open", index=True)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        index=True,
    )


class Report(Base):
    """Stores generated reporting snapshots for an organization."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    generated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        index=True,
    )
    period_start: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    summary_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    delivered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

