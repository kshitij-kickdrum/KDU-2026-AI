from __future__ import annotations

import re

try:
    import nltk
except Exception:  # noqa: BLE001
    nltk = None  # type: ignore[assignment]


def ensure_nltk() -> None:
    if nltk is None:
        return
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        try:
            nltk.download("punkt", quiet=True)
        except Exception:  # noqa: BLE001
            return
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        try:
            nltk.download("punkt_tab", quiet=True)
        except Exception:  # noqa: BLE001
            return


def sentence_split(text: str) -> list[str]:
    if nltk is None:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s.strip() for s in sentences if s.strip()]
    try:
        ensure_nltk()
        sentences = nltk.sent_tokenize(text)
        return [s.strip() for s in sentences if s.strip()]
    except Exception:  # noqa: BLE001
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s.strip() for s in sentences if s.strip()]


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE)


def token_count(text: str) -> int:
    return len(tokenize(text))


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
