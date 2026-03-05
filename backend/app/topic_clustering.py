from __future__ import annotations

from pathlib import Path
from typing import List, Union

from app.topic_keywords import keyword_topic

# Optional ML imports (CI-safe)
try:
    from bertopic import BERTopic
    from sentence_transformers import SentenceTransformer
except ImportError:
    BERTopic = None
    SentenceTransformer = None


MODEL_DIR = Path("ml-models")
MODEL_DIR.mkdir(exist_ok=True)

MODEL_PATH = MODEL_DIR / "cxmind_topic_model"


# Cached models
_topic_model = None
_embedding_model = None


def _get_embedding_model():
    """Lazy load embedding model"""
    global _embedding_model

    if _embedding_model is None:
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers not installed")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    return _embedding_model


def train_topic_model(texts: List[str]):
    """Train BERTopic model"""

    if BERTopic is None:
        raise RuntimeError("BERTopic not installed")

    embedding_model = _get_embedding_model()

    topic_model = BERTopic(
        embedding_model=embedding_model,
        min_topic_size=2,
        nr_topics=6,
        verbose=True
    )

    topics, probs = topic_model.fit_transform(texts)

    topic_model.save(MODEL_PATH)

    global _topic_model
    _topic_model = topic_model

    return topic_model


def load_topic_model():
    """Load trained topic model safely"""

    global _topic_model

    if _topic_model is None:

        if BERTopic is None:
            return None

        embedding_model = _get_embedding_model()

        try:
            _topic_model = BERTopic.load(
                MODEL_PATH,
                embedding_model=embedding_model
            )
        except Exception:
            return None

    return _topic_model


def predict_topic(text: str) -> Union[int, str]:
    """
    Predict topic for new text.
    First try keyword detection.
    """

    # keyword detection first
    keyword_result = keyword_topic(text)

    if keyword_result is not None:
        return keyword_result

    model = load_topic_model()

    # CI-safe fallback
    if model is None:
        return "general_feedback"

    try:
        topics, probs = model.transform([text])
        return int(topics[0]) if topics else 0
    except Exception:
        return "general_feedback"


def get_topic_label(topic_id: Union[int, str]) -> str:
    """
    Convert topic id to readable label
    """

    # if keyword topic already
    if isinstance(topic_id, str):
        return topic_id

    model = load_topic_model()

    if model is None:
        return "general_feedback"

    try:
        topic_words = model.get_topic(topic_id) or []

        if not topic_words:
            return "general_feedback"

        keywords = [word for word, _ in topic_words[:3]]

        return "_".join(keywords)

    except Exception:
        return "general_feedback"