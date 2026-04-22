import re

from app.utils.errors import ValidationError


def validate_message(message: str) -> str:
    cleaned = (message or "").strip()
    if not cleaned:
        raise ValidationError("message is required")
    if len(cleaned) > 4000:
        raise ValidationError("message is too long")
    # Minimal input sanitization for obvious control payloads.
    if re.search(r"(<script|</script|DROP TABLE|--\s)", cleaned, re.IGNORECASE):
        raise ValidationError("message contains unsafe input patterns")
    return cleaned


def validate_session_id(session_id: str) -> str:
    cleaned = (session_id or "").strip()
    if not cleaned:
        raise ValidationError("session_id is required")
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,128}", cleaned):
        raise ValidationError("session_id format is invalid")
    return cleaned

