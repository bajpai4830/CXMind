from __future__ import annotations

import os
import threading
from dataclasses import dataclass

try:
    from transformers import pipeline as hf_pipeline  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    hf_pipeline = None


_lock = threading.Lock()
_zero_shot_pipe = None


def _allow_model_downloads() -> bool:
    return (os.environ.get("CXMIND_ALLOW_MODEL_DOWNLOADS") or "").strip().lower() in {"1", "true", "yes"}


def _get_backend() -> str:
    # auto|zero-shot|rules
    return (os.environ.get("CXMIND_INTENT_BACKEND") or "auto").strip().lower()


def _get_model() -> str:
    return (os.environ.get("CXMIND_INTENT_MODEL") or "facebook/bart-large-mnli").strip()


@dataclass(frozen=True)
class IntentScore:
    intent: str
    confidence: float
    model_name: str


_CANDIDATES = [
    "refund_request",
    "billing_issue",
    "technical_support",
    "delivery_issue",
    "account_access",
    "cancellation",
    "product_inquiry",
    "praise",
    "complaint",
    "information_request",
]


def _load_zero_shot():
    global _zero_shot_pipe
    if _zero_shot_pipe is not None:
        return _zero_shot_pipe
    if hf_pipeline is None:
        raise RuntimeError("transformers is not installed")
    model_id = _get_model()
    local_only = not _allow_model_downloads()
    with _lock:
        if _zero_shot_pipe is None:
            try:
                from transformers import AutoModelForSequenceClassification, AutoTokenizer  # type: ignore

                tok = AutoTokenizer.from_pretrained(model_id, local_files_only=local_only)
                mdl = AutoModelForSequenceClassification.from_pretrained(model_id, local_files_only=local_only)
                _zero_shot_pipe = hf_pipeline("zero-shot-classification", model=mdl, tokenizer=tok)
            except Exception:
                if local_only:
                    raise
                _zero_shot_pipe = hf_pipeline("zero-shot-classification", model=model_id)
    return _zero_shot_pipe


def _rules_intent(text: str, *, channel: str | None = None) -> IntentScore:
    t = (text or "").lower()

    def hit(words: list[str]) -> bool:
        return any(w in t for w in words)

    if hit(["refund", "money back", "return", "chargeback"]):
        return IntentScore(intent="refund_request", confidence=0.85, model_name="rules:v1")
    if hit(["invoice", "billing", "charged", "charge", "payment", "transaction", "card"]):
        return IntentScore(intent="billing_issue", confidence=0.8, model_name="rules:v1")
    if hit(["crash", "bug", "error", "issue", "freeze", "slow", "lag", "broken", "not working"]):
        return IntentScore(intent="technical_support", confidence=0.78, model_name="rules:v1")
    if hit(["login", "sign in", "password", "otp", "verification", "activate", "activation"]):
        return IntentScore(intent="account_access", confidence=0.78, model_name="rules:v1")
    if hit(["delivery", "delivered", "shipment", "shipping", "courier", "tracking", "late", "delay"]):
        return IntentScore(intent="delivery_issue", confidence=0.75, model_name="rules:v1")
    if hit(["cancel", "unsubscribe", "close my account", "stop using"]):
        return IntentScore(intent="cancellation", confidence=0.8, model_name="rules:v1")
    if hit(["love", "great", "awesome", "amazing", "thank you", "thanks", "impressed"]):
        return IntentScore(intent="praise", confidence=0.72, model_name="rules:v1")
    if hit(["price", "pricing", "plan", "features", "how much", "trial"]):
        return IntentScore(intent="product_inquiry", confidence=0.62, model_name="rules:v1")
    if "?" in t or hit(["how do i", "can you", "could you", "please explain", "not sure"]):
        return IntentScore(intent="information_request", confidence=0.55, model_name="rules:v1")

    # Channel hints
    if channel in {"support_ticket", "email"}:
        return IntentScore(intent="complaint", confidence=0.5, model_name="rules:v1")

    return IntentScore(intent="complaint", confidence=0.35, model_name="rules:v1")


def classify(text: str, *, channel: str | None = None) -> IntentScore:
    text = (text or "").strip()
    if not text:
        return IntentScore(intent="information_request", confidence=0.0, model_name="none")

    backend = _get_backend()
    if backend in {"auto", "zero-shot"}:
        try:
            pipe = _load_zero_shot()
            out = pipe(text[:1024], candidate_labels=_CANDIDATES, multi_label=False)
            labels = out.get("labels") or []
            scores = out.get("scores") or []
            if labels and scores:
                return IntentScore(intent=str(labels[0]), confidence=float(scores[0]), model_name=f"hf:{_get_model()}")
        except Exception:
            if backend == "zero-shot":
                raise

    return _rules_intent(text, channel=channel)
