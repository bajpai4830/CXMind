from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import (
    EmotionResult,
    IntentResult,
    Interaction,
    JourneyEvent,
    Recommendation,
    SentimentResult,
    TopicResult,
)
from app.services import emotion_service, intent_service, journey_service, recommendation_service, sentiment_service, topic_service


def enrich_interaction(db: Session, interaction: Interaction) -> None:
    # Sentiment
    sent = sentiment_service.score(interaction.text)
    interaction.sentiment_label = sent.label
    interaction.sentiment_compound = sent.compound
    db.add(
        SentimentResult(
            interaction_id=interaction.id,
            model_name=sent.model_name,
            sentiment=sent.label,
            confidence=sent.confidence,
            compound=sent.compound,
        )
    )

    # Topic
    topic = topic_service.detect_topic(interaction.text, sentiment_label=sent.label)
    interaction.topic = topic.topic
    topic_dim = topic_service.ensure_topic_dim(db, topic.topic)
    db.add(
        TopicResult(
            interaction_id=interaction.id,
            topic_id=topic_dim.id,
            model_name=topic.model_name,
            topic=topic.topic,
            confidence=topic.confidence,
        )
    )

    # Emotion
    emo = emotion_service.detect(interaction.text, sentiment_label=sent.label)
    db.add(
        EmotionResult(
            interaction_id=interaction.id,
            model_name=emo.model_name,
            emotion=emo.emotion,
            confidence=emo.confidence,
        )
    )

    # Intent
    intent = intent_service.classify(interaction.text, channel=interaction.channel)
    db.add(
        IntentResult(
            interaction_id=interaction.id,
            model_name=intent.model_name,
            intent=intent.intent,
            confidence=intent.confidence,
        )
    )

    # Journey stage (mapped from signals)
    stage = journey_service.map_stage(
        text=interaction.text,
        channel=interaction.channel,
        topic=topic.topic,
        intent=intent.intent,
    )
    db.add(
        JourneyEvent(
            customer_id=interaction.customer_id,
            interaction_id=interaction.id,
            session_id=interaction.session_id,
            stage=stage.stage,
            stage_method=stage.method,
            confidence=stage.confidence,
            occurred_at=interaction.occurred_at or interaction.created_at,
        )
    )

    # Recommendations
    recs = recommendation_service.recommend(
        topic=topic.topic,
        sentiment_label=sent.label,
        stage=stage.stage,
        intent=intent.intent,
    )
    for r in recs:
        db.add(
            Recommendation(
                customer_id=interaction.customer_id,
                interaction_id=interaction.id,
                stage=stage.stage,
                topic=topic.topic,
                recommendation=r.recommendation,
                priority=r.priority,
            )
        )

