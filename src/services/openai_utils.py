from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

from openai import APIStatusError, APITimeoutError, RateLimitError

T = TypeVar("T")
logger = logging.getLogger(__name__)


def call_openai_with_retry(func: Callable[[], T], max_retries: int = 3, base_delay: int = 2) -> T:
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return func()
        except (RateLimitError, APITimeoutError, APIStatusError) as exc:
            is_retryable = not isinstance(exc, APIStatusError) or (exc.status_code >= 500)
            if not is_retryable:
                raise
            last_error = exc
            if attempt >= max_retries:
                break
            delay = base_delay * (2**attempt)
            logger.warning("OpenAI retry attempt %s/%s in %ss: %s", attempt + 1, max_retries, delay, exc)
            time.sleep(delay)
    raise RuntimeError(f"OpenAI API failed after retries: {last_error}") from last_error
