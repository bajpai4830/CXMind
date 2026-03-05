from __future__ import annotations

from pathlib import Path
from typing import List, Union

from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

from app.topic_keywords import keyword_topic


# Directory where the trained topic model will be saved
MODEL_DIR = Path("ml-models")
MODEL_DIR.mkdir(exist_ok=True)

MODEL_PATH = MODEL_DIR / "cxmind_topic_model"


# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


# Cache model in memory (avoid loading every request)
_topic_model: BERTopic | None = None


def train_topic_model(texts: List[str]) -> BERTopic:
    """
    Train a BERTopic model on interaction texts.
    """

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


def load_topic_model() -> BERTopic:
    """
    Load trained topic model (cached).
    """

    global _topic_model

    if _topic_model is None:
        _topic_model = BERTopic.load(MODEL_PATH, embedding_model=embedding_model)

    return _topic_model


def predict_topic(text: str) -> Union[int, str]:
    """
    Predict topic for new text.

    First try keyword-based detection.
    If no keyword matches, fallback to BERTopic clustering.
    """

    # 1️⃣ Keyword detection
    keyword_result = keyword_topic(text)

    if keyword_result is not None:
        return keyword_result

    # 2️⃣ Fallback to BERTopic clustering
    model = load_topic_model()

    topics, probs = model.transform([text])

    return int(topics[0])


def get_topic_label(topic_id: Union[int, str]) -> str:
    """
    Convert topic ID into readable label.
    If topic already comes from keyword detection, return it directly.
    """

    # If topic is already a string (keyword topic)
    if isinstance(topic_id, str):
        return topic_id

    model = load_topic_model()

    topic_words = model.get_topic(topic_id)

    if not topic_words:
        return "unknown"

    # Take top 3 keywords
    keywords = [word for word, _ in topic_words[:3]]

    return "_".join(keywords)