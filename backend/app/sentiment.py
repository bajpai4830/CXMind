from __future__ import annotations

from dataclasses import dataclass

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


@dataclass(frozen=True)
class SentimentResult:
    compound: float
    label: str


_analyzer = SentimentIntensityAnalyzer()


def score_text(text: str) -> SentimentResult:
    # VADER expects natural language; keep as-is except trimming.
    text = (text or "").strip()
    if not text:
        return SentimentResult(compound=0.0, label="neutral")

    compound = float(_analyzer.polarity_scores(text)["compound"])

    # Common VADER thresholds.
    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return SentimentResult(compound=compound, label=label)

