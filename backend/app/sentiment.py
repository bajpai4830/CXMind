from __future__ import annotations

from dataclasses import dataclass
from transformers import pipeline


@dataclass(frozen=True)
class SentimentResult:
    compound: float
    label: str


transformer_pipeline = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english"
)


def score_text(text: str) -> SentimentResult:
    text = (text or "").strip()
    if not text:
        return SentimentResult(compound=0.0, label="neutral")

    result = transformer_pipeline(text)[0]

    label = result["label"].lower()
    score = float(result["score"])

    if label == "positive":
        compound = score
    else:
        compound = -score

    return SentimentResult(compound=compound, label=label)