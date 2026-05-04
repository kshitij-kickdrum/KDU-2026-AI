from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass


class ConcurrencyTimeoutError(TimeoutError):
    pass


@dataclass
class ConcurrencyQueue:
    max_concurrent: int
    timeout_seconds: float = 5.0

    def __post_init__(self) -> None:
        self._semaphore = asyncio.Semaphore(self.max_concurrent)

    @asynccontextmanager
    async def acquire(self):
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=self.timeout_seconds)
        except asyncio.TimeoutError as exc:
            raise ConcurrencyTimeoutError(
                f"Queue slot not available within {self.timeout_seconds}s"
            ) from exc
        try:
            yield
        finally:
            self._semaphore.release()

