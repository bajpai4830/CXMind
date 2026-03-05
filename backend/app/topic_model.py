from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import numpy as np

# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Predefined topic centers (initial seeds)
TOPIC_LABELS = [
    "delivery_issue",
    "customer_support",
    "billing_problem",
    "technical_issue",
    "general_feedback"
]

topic_embeddings = embedding_model.encode(TOPIC_LABELS)


def detect_topic(text: str) -> str:
    """
    Detects the closest topic using embedding similarity.
    """
    text_embedding = embedding_model.encode([text])[0]

    similarities = np.dot(topic_embeddings, text_embedding)

    topic_index = np.argmax(similarities)

    return TOPIC_LABELS[topic_index]