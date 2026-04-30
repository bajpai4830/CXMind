from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass

_lock = threading.Lock()
_pipe = None


def _allow_model_downloads() -> bool:
    return (os.environ.get("CXMIND_ALLOW_MODEL_DOWNLOADS") or "").strip().lower() in {"1", "true", "yes"}


def _get_backend() -> str:
    # auto|transformer|rules
    return (os.environ.get("CXMIND_EMOTION_BACKEND") or "auto").strip().lower()


def _get_model() -> str:
    # Common HF emotion model.
    return (os.environ.get("CXMIND_EMOTION_MODEL") or "j-hartmann/emotion-english-distilroberta-base").strip()


@dataclass(frozen=True)
class EmotionScore:
    emotion: str  # anger|frustration|satisfaction|confusion|joy
    confidence: float
    model_name: str


_KEYWORDS: dict[str, list[str]] = {
    "anger": ["angry", "furious", "outrage", "ridiculous", "unacceptable", "hate"],
    "frustration": ["frustrated", "annoyed", "irritating", "fed up", "stuck", "wasted", "terrible"],
    "confusion": ["confused", "unclear", "not sure", "don't understand", "how do i", "why does", "what is this"],
    "joy": ["love", "awesome", "great", "amazing", "happy", "delighted", "impressed", "perfect"],
    "satisfaction": ["satisfied", "pleased", "thank you", "thanks", "resolved", "worked", "good"],
}


def _rules_emotion(text: str, sentiment_label: str | None = None) -> EmotionScore:
    t = (text or "").lower()

    # Keyword match with a simple scoring.
    best = ("satisfaction", 0)
    for emo, words in _KEYWORDS.items():
        hits = sum(1 for w in words if w in t)
        if hits > best[1]:
            best = (emo, hits)

    if best[1] > 0:
        conf = min(1.0, 0.55 + 0.15 * best[1])
        return EmotionScore(emotion=best[0], confidence=conf, model_name="rules:v1")

    # Heuristic fallback by sentiment polarity.
    if sentiment_label == "negative":
        return EmotionScore(emotion="frustration", confidence=0.45, model_name="rules:v1")
    if sentiment_label == "positive":
        return EmotionScore(emotion="satisfaction", confidence=0.45, model_name="rules:v1")
    return EmotionScore(emotion="confusion", confidence=0.35, model_name="rules:v1")


def _load_transformer():
    global _pipe
    if _pipe is not None:
        return _pipe
        
    try:
        from transformers import pipeline as hf_pipeline
    except Exception:
        raise RuntimeError("transformers is not installed")
        
    model = _get_model()
    with _lock:
        if _pipe is None:
            local_only = not _allow_model_downloads()
            try:
                from transformers import AutoModelForSequenceClassification, AutoTokenizer  # type: ignore

                tok = AutoTokenizer.from_pretrained(model, local_files_only=local_only)
                mdl = AutoModelForSequenceClassification.from_pretrained(model, local_files_only=local_only)
                _pipe = hf_pipeline("text-classification", model=mdl, tokenizer=tok, top_k=1)
            except Exception:
                if local_only:
                    raise
                _pipe = hf_pipeline("text-classification", model=model, top_k=1)
    return _pipe


_HF_TO_PLATFORM = {
    "anger": "anger",
    "joy": "joy",
    "neutral": "satisfaction",
    "sadness": "frustration",
    "disgust": "frustration",
    "fear": "confusion",
    "surprise": "confusion",
}


def detect(text: str, *, sentiment_label: str | None = None) -> EmotionScore:
    text = (text or "").strip()
    if not text:
        return EmotionScore(emotion="satisfaction", confidence=0.0, model_name="none")

    backend = _get_backend()
    if backend in {"auto", "transformer"}:
        try:
            pipe = _load_transformer()
            out = pipe(text[:1024])
            # HF returns either list[dict] or list[list[dict]] depending on top_k usage.
            if out and isinstance(out[0], list):
                best = out[0][0]
            else:
                best = out[0]

            label = str(best.get("label", "neutral")).lower()
            # Some models use labels like "LABEL_0". If so, fall back to rules.
            if re.match(r"^label_\\d+$", label):
                return _rules_emotion(text, sentiment_label)

            mapped = _HF_TO_PLATFORM.get(label, "confusion")
            conf = float(best.get("score", 0.0))
            return EmotionScore(emotion=mapped, confidence=max(0.0, min(1.0, conf)), model_name=f"hf:{_get_model()}")
        except Exception:
            if backend == "transformer":
                raise

    return _rules_emotion(text, sentiment_label)
