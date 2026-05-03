"""Input validation helpers shared by app entrypoints."""

from __future__ import annotations

import re


TOPIC_PATTERN = re.compile(r"^[A-Za-z0-9\s.,:;!?()'\"/_+-]+$")


def validate_topic(topic: str) -> str:
    """Validate topic length and allowed characters.

    Args:
        topic: User-provided research topic.

    Returns:
        Sanitized topic.

    Raises:
        ValueError: If the topic is empty, too long, or contains disallowed
            characters.
    """
    cleaned = topic.strip()
    if not cleaned:
        raise ValueError("topic: expected non-empty string")
    if len(cleaned) > 500:
        raise ValueError("topic: expected max 500 characters")
    if not TOPIC_PATTERN.match(cleaned):
        raise ValueError(
            "topic: expected alphanumeric text with common punctuation only"
        )
    return cleaned
