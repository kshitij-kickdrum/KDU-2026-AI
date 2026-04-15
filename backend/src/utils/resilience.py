from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_seconds: int = 60
    failures: int = 0
    open_until: float = 0.0

    def can_call(self) -> bool:
        return time.time() >= self.open_until

    def on_success(self) -> None:
        self.failures = 0
        self.open_until = 0.0

    def on_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.open_until = time.time() + self.recovery_seconds


def retry(
    fn: Callable[[], T],
    attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
) -> T:
    last_error: Exception | None = None
    delay = initial_delay
    for _ in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(delay)
            delay = min(delay * 2, max_delay)
    if last_error:
        raise last_error
    raise RuntimeError("retry failed with no attempts")

