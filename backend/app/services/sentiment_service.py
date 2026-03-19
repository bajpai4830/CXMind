from __future__ import annotations

import os
import threading
from dataclasses import dataclass


try:
    from transformers import pipeline as hf_pipeline  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    hf_pipeline = None

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    SentimentIntensityAnalyzer = None


_lock = threading.Lock()
_transformer_pipe = None
_vader = None


def _allow_model_downloads() -> bool:
    return (os.environ.get("CXMIND_ALLOW_MODEL_DOWNLOADS") or "").strip().lower() in {"1", "true", "yes"}


def _get_sentiment_backend() -> str:
    # auto|transformer|vader
    return (os.environ.get("CXMIND_SENTIMENT_BACKEND") or "auto").strip().lower()


def _get_transformer_model() -> str:
    return (os.environ.get("CXMIND_SENTIMENT_MODEL") or "distilbert-base-uncased-finetuned-sst-2-english").strip()


@dataclass(frozen=True)
class SentimentScore:
    label: str  # positive|neutral|negative
    compound: float  # in [-1, 1]
    confidence: float  # in [0, 1]
    model_name: str


def _load_transformer():
    global _transformer_pipe
    if _transformer_pipe is not None:
        return _transformer_pipe
    if hf_pipeline is None:
        raise RuntimeError("transformers is not installed")

    model_id = _get_transformer_model()
    local_only = not _allow_model_downloads()
    with _lock:
        if _transformer_pipe is None:
            try:
                from transformers import AutoModelForSequenceClassification, AutoTokenizer  # type: ignore

                tok = AutoTokenizer.from_pretrained(model_id, local_files_only=local_only)
                mdl = AutoModelForSequenceClassification.from_pretrained(model_id, local_files_only=local_only)
                _transformer_pipe = hf_pipeline("sentiment-analysis", model=mdl, tokenizer=tok)
            except Exception:
                # Fall back to pipeline loading (may download if allowed).
                if local_only:
                    raise
                _transformer_pipe = hf_pipeline("sentiment-analysis", model=model_id)
    return _transformer_pipe


def _load_vader():
    global _vader
    if _vader is not None:
        return _vader
    if SentimentIntensityAnalyzer is None:
        raise RuntimeError("vaderSentiment is not installed")
    with _lock:
        if _vader is None:
            _vader = SentimentIntensityAnalyzer()
    return _vader


def _label_from_compound(compound: float) -> str:
    # Standard VADER thresholds.
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"


def score(text: str) -> SentimentScore:
    text = (text or "").strip()
    if not text:
        return SentimentScore(label="neutral", compound=0.0, confidence=0.0, model_name="none")

    backend = _get_sentiment_backend()

    if backend in {"auto", "transformer"}:
        try:
            pipe = _load_transformer()
            # Keep a reasonable bound for model inputs; most sentiment models are trained on short texts.
            result = pipe(text[:1024])[0]

            raw_label = str(result.get("label", "neutral")).lower()
            conf = float(result.get("score", 0.0))
            compound = conf if raw_label == "positive" else -conf

            # The SST-2 family is binary. Add a neutral band for UX/analytics.
            label = _label_from_compound(compound)
            return SentimentScore(
                label=label,
                compound=float(max(-1.0, min(1.0, compound))),
                confidence=float(max(0.0, min(1.0, conf))),
                model_name=f"hf:{_get_transformer_model()}",
            )
        except Exception:
            if backend == "transformer":
                raise

    # Fallback: VADER (fast, no model download).
    vader = _load_vader()
    scores = vader.polarity_scores(text)
    compound = float(scores.get("compound", 0.0))
    return SentimentScore(
        label=_label_from_compound(compound),
        compound=float(max(-1.0, min(1.0, compound))),
        confidence=float(min(1.0, abs(compound))),
        model_name="vaderSentiment",
    )
