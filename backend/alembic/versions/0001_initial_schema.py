"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-03-15
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=True),
        sa.Column("signup_date", sa.Date(), nullable=True),
        sa.Column("region", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_customers_created_at"), "customers", ["created_at"], unique=False)
    op.create_index(op.f("ix_customers_customer_id"), "customers", ["customer_id"], unique=True)
    op.create_index(op.f("ix_customers_region"), "customers", ["region"], unique=False)

    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("label"),
    )
    op.create_index(op.f("ix_topics_created_at"), "topics", ["created_at"], unique=False)
    op.create_index(op.f("ix_topics_label"), "topics", ["label"], unique=True)

    op.create_table(
        "interactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.String(length=128), nullable=True),
        sa.Column("channel", sa.String(length=64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("interaction_type", sa.String(length=64), nullable=True),
        sa.Column("session_id", sa.String(length=128), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("sentiment_compound", sa.Float(), nullable=False),
        sa.Column("sentiment_label", sa.String(length=16), nullable=False),
        sa.Column("topic", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.customer_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interactions_channel"), "interactions", ["channel"], unique=False)
    op.create_index(op.f("ix_interactions_created_at"), "interactions", ["created_at"], unique=False)
    op.create_index(op.f("ix_interactions_customer_id"), "interactions", ["customer_id"], unique=False)
    op.create_index(op.f("ix_interactions_interaction_type"), "interactions", ["interaction_type"], unique=False)
    op.create_index(op.f("ix_interactions_occurred_at"), "interactions", ["occurred_at"], unique=False)
    op.create_index(op.f("ix_interactions_sentiment_label"), "interactions", ["sentiment_label"], unique=False)
    op.create_index(op.f("ix_interactions_session_id"), "interactions", ["session_id"], unique=False)
    op.create_index(op.f("ix_interactions_topic"), "interactions", ["topic"], unique=False)

    op.create_table(
        "cx_risk_predictions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.String(length=128), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.Column("features", sa.JSON(), nullable=True),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cx_risk_predictions_as_of"), "cx_risk_predictions", ["as_of"], unique=False)
    op.create_index(op.f("ix_cx_risk_predictions_customer_id"), "cx_risk_predictions", ["customer_id"], unique=False)
    op.create_index(op.f("ix_cx_risk_predictions_risk_level"), "cx_risk_predictions", ["risk_level"], unique=False)

    op.create_table(
        "emotion_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("interaction_id", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("emotion", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["interaction_id"], ["interactions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_emotion_results_created_at"), "emotion_results", ["created_at"], unique=False)
    op.create_index(op.f("ix_emotion_results_emotion"), "emotion_results", ["emotion"], unique=False)
    op.create_index(op.f("ix_emotion_results_interaction_id"), "emotion_results", ["interaction_id"], unique=False)

    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("interaction_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=256), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["interaction_id"], ["interactions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_feedback_created_at"), "feedback", ["created_at"], unique=False)
    op.create_index(op.f("ix_feedback_interaction_id"), "feedback", ["interaction_id"], unique=False)
    op.create_index(op.f("ix_feedback_rating"), "feedback", ["rating"], unique=False)
    op.create_index(op.f("ix_feedback_source"), "feedback", ["source"], unique=False)

    op.create_table(
        "intent_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("interaction_id", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("intent", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["interaction_id"], ["interactions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_intent_results_created_at"), "intent_results", ["created_at"], unique=False)
    op.create_index(op.f("ix_intent_results_intent"), "intent_results", ["intent"], unique=False)
    op.create_index(op.f("ix_intent_results_interaction_id"), "intent_results", ["interaction_id"], unique=False)

    op.create_table(
        "journey_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.String(length=128), nullable=True),
        sa.Column("interaction_id", sa.Integer(), nullable=True),
        sa.Column("session_id", sa.String(length=128), nullable=True),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column("stage_method", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["interaction_id"], ["interactions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_journey_events_customer_id"), "journey_events", ["customer_id"], unique=False)
    op.create_index(op.f("ix_journey_events_occurred_at"), "journey_events", ["occurred_at"], unique=False)
    op.create_index(op.f("ix_journey_events_session_id"), "journey_events", ["session_id"], unique=False)
    op.create_index(op.f("ix_journey_events_stage"), "journey_events", ["stage"], unique=False)

    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.String(length=128), nullable=True),
        sa.Column("interaction_id", sa.Integer(), nullable=True),
        sa.Column("stage", sa.String(length=64), nullable=True),
        sa.Column("topic", sa.String(length=128), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["interaction_id"], ["interactions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recommendations_created_at"), "recommendations", ["created_at"], unique=False)
    op.create_index(op.f("ix_recommendations_customer_id"), "recommendations", ["customer_id"], unique=False)
    op.create_index(op.f("ix_recommendations_interaction_id"), "recommendations", ["interaction_id"], unique=False)
    op.create_index(op.f("ix_recommendations_priority"), "recommendations", ["priority"], unique=False)
    op.create_index(op.f("ix_recommendations_stage"), "recommendations", ["stage"], unique=False)
    op.create_index(op.f("ix_recommendations_status"), "recommendations", ["status"], unique=False)
    op.create_index(op.f("ix_recommendations_topic"), "recommendations", ["topic"], unique=False)

    op.create_table(
        "sentiment_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("interaction_id", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("sentiment", sa.String(length=16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("compound", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["interaction_id"], ["interactions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sentiment_results_created_at"), "sentiment_results", ["created_at"], unique=False)
    op.create_index(op.f("ix_sentiment_results_interaction_id"), "sentiment_results", ["interaction_id"], unique=False)
    op.create_index(op.f("ix_sentiment_results_sentiment"), "sentiment_results", ["sentiment"], unique=False)

    op.create_table(
        "topic_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("interaction_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("topic", sa.String(length=128), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["interaction_id"], ["interactions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_topic_results_created_at"), "topic_results", ["created_at"], unique=False)
    op.create_index(op.f("ix_topic_results_interaction_id"), "topic_results", ["interaction_id"], unique=False)
    op.create_index(op.f("ix_topic_results_topic"), "topic_results", ["topic"], unique=False)


def downgrade() -> None:
    op.drop_table("topic_results")
    op.drop_table("sentiment_results")
    op.drop_table("recommendations")
    op.drop_table("journey_events")
    op.drop_table("intent_results")
    op.drop_table("feedback")
    op.drop_table("emotion_results")
    op.drop_table("cx_risk_predictions")
    op.drop_table("interactions")
    op.drop_table("topics")
    op.drop_table("customers")
