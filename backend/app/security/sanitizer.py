import re

from app.core.exceptions import InvalidInput
from app.core.logging import get_logger

logger = get_logger(__name__)

_INJECTION_PATTERNS = re.compile(
    r"(ignore (all )?(previous|prior|above) instructions?|"
    r"forget (all )?instructions?|"
    r"you are now\b|"
    r"pretend (you are|to be)\b|"
    r"roleplay as\b|"
    r"act as (a |an )?\w+|"
    r"disregard (all )?instructions?|"
    r"jailbreak|"
    r"bypass (all )?(your )?(rules?|guidelines?|restrictions?))",
    re.IGNORECASE,
)

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_input(text: str) -> str:
    """Strip control characters and reject prompt injection attempts."""
    cleaned = _CONTROL_CHARS.sub("", text)

    if _INJECTION_PATTERNS.search(cleaned):
        logger.warning("prompt_injection_detected", snippet=cleaned[:120])
        raise InvalidInput("Input contains disallowed instructions.")

    return cleaned
