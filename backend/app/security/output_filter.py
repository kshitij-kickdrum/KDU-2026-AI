import re

from app.core.logging import get_logger

logger = get_logger(__name__)

_EMAIL = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE = re.compile(r"\b(\+?[\d][\d\s\-().]{8,}\d)\b")


def filter_pii(text: str) -> str:
    """Redact emails and phone numbers from LLM output."""
    result = _EMAIL.sub("[EMAIL REDACTED]", text)
    result = _PHONE.sub("[PHONE REDACTED]", result)
    if result != text:
        logger.info("pii_redacted_from_output")
    return result


def filter_parsed(parsed: dict) -> dict:
    """Apply PII filtering to all string values in a parsed response dict."""
    return {
        k: filter_pii(v) if isinstance(v, str) else v
        for k, v in parsed.items()
    }
