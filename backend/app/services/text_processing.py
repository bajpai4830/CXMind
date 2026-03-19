from __future__ import annotations

import re
import threading

try:  # optional dependency
    import spacy  # type: ignore
except Exception:  # pragma: no cover
    spacy = None


_lock = threading.Lock()
_nlp = None


def _load_spacy():
    global _nlp
    if _nlp is not None:
        return _nlp
    if spacy is None:
        raise RuntimeError("spaCy not installed")
    with _lock:
        if _nlp is None:
            # Use a small model name if available. If not installed, caller will fall back.
            _nlp = spacy.load("en_core_web_sm")
    return _nlp


def clean_text(text: str) -> str:
    t = (text or "").lower()
    t = re.sub(r"http\\S+", "", t)
    t = re.sub(r"[^a-z0-9\\s]", " ", t)
    t = re.sub(r"\\s+", " ", t).strip()
    return t


def tokenize(text: str) -> list[str]:
    t = clean_text(text)
    if not t:
        return []
    return t.split()


def lemmatize_remove_stopwords(text: str) -> list[str]:
    # If spaCy isn't available, fall back to basic tokenization.
    try:
        nlp = _load_spacy()
    except Exception:
        return tokenize(text)

    doc = nlp(text or "")
    out: list[str] = []
    for tok in doc:
        if tok.is_space or tok.is_punct:
            continue
        if tok.is_stop:
            continue
        lemma = tok.lemma_.strip().lower()
        if not lemma or lemma == "-pron-":
            continue
        out.append(lemma)
    return out

