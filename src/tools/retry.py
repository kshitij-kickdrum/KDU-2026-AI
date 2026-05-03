"""Retry helper with exponential backoff."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from src.utils.logger import get_logger

T = TypeVar("T")
logger = get_logger(__name__)


def with_exponential_backoff(
    func: Callable[[], T], max_retries: int = 3, base_delay: float = 1.0
) -> T | None:
    """Retry a zero-argument callable on TimeoutError."""
    for attempt in range(max_retries + 1):
        try:
            return func()
        except TimeoutError as exc:
            logger.error("TimeoutError on attempt %s: %s", attempt + 1, exc)
            if attempt >= max_retries:
                logger.warning(
                    "Maximum retries exceeded; continuing without tool output"
                )
                return None
            delay = base_delay * (2**attempt)
            logger.info("Retry attempt %s after %.1fs", attempt + 1, delay)
            time.sleep(delay)
    return None
