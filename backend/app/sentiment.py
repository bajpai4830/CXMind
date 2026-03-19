from __future__ import annotations

from dataclasses import dataclass

from app.services import sentiment_service


@dataclass(frozen=True)
class SentimentResult:
    compound: float
    label: str

def score_text(text: str) -> SentimentResult:
    s = sentiment_service.score(text)
    return SentimentResult(compound=s.compound, label=s.label)
