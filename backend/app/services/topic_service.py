from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import Topic as TopicDim
from app.topic_cleaner import clean_topic
from app.topic_clustering import get_topic_label, predict_topic
from app.topic_keywords import keyword_topic
from app.topic_normalizer import normalize_topic


@dataclass(frozen=True)
class TopicScore:
    topic: str
    confidence: float
    method: str  # keyword|bertopic|fallback
    model_name: str


def _upsert_topic_dim(db: Session, label: str) -> TopicDim:
    existing = db.query(TopicDim).filter(TopicDim.label == label).one_or_none()
    if existing is not None:
        return existing
    row = TopicDim(label=label)
    db.add(row)
    db.flush()
    return row


def detect_topic(text: str, *, sentiment_label: str) -> TopicScore:
    # Keywords first for deterministic mappings.
    topic = keyword_topic(text)
    if topic is not None:
        return TopicScore(topic=normalize_topic(topic), confidence=0.9, method="keyword", model_name="rules:v1")

    topic_id = predict_topic(text)
    if isinstance(topic_id, str):
        return TopicScore(topic=normalize_topic(topic_id), confidence=0.55, method="fallback", model_name="fallback")

    raw_topic = get_topic_label(topic_id)
    cleaned = clean_topic(raw_topic, text, sentiment_label)
    return TopicScore(topic=normalize_topic(cleaned), confidence=0.6, method="bertopic", model_name="bertopic")


def ensure_topic_dim(db: Session, label: str) -> TopicDim:
    return _upsert_topic_dim(db, label)

