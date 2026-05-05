from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from src.core.exceptions import CircuitBreakerOpenError
from src.storage.database import Database
from src.utils.config import CircuitBreakerConfig

LOGGER = logging.getLogger(__name__)

FALLBACK_RESPONSE = (
    "I'm unable to access that tool right now due to repeated failures. "
    "Please try again later or contact support if the issue persists."
)


class CircuitBreaker:
    def __init__(self, database: Database, config: CircuitBreakerConfig) -> None:
        self.database = database
        self.threshold = config.threshold
        self.timeout = timedelta(seconds=config.timeout_seconds)

    def is_open(self, tool_name: str) -> bool:
        row = self.database.fetch_one(
            "SELECT state, last_failure_at FROM circuit_breaker_state WHERE tool_name = ?",
            (tool_name,),
        )
        if row is None:
            return False
        if row["state"] != "open":
            return False
        last_failure = row["last_failure_at"]
        if not last_failure:
            return True
        failure_time = datetime.fromisoformat(last_failure)
        if datetime.now(UTC) - failure_time >= self.timeout:
            self._set_half_open(tool_name)
            return False
        return True

    def ensure_allowed(self, tool_name: str) -> None:
        if self.is_open(tool_name):
            raise CircuitBreakerOpenError(FALLBACK_RESPONSE)

    def record_failure(self, tool_name: str) -> int:
        now = datetime.now(UTC).isoformat()
        row = self.database.fetch_one(
            "SELECT failure_count FROM circuit_breaker_state WHERE tool_name = ?",
            (tool_name,),
        )
        failure_count = int(row["failure_count"]) + 1 if row else 1
        state = "open" if failure_count >= self.threshold else "closed"
        self.database.execute(
            """
            INSERT INTO circuit_breaker_state (
                tool_name, failure_count, state, last_failure_at
            ) VALUES (?, ?, ?, ?)
            ON CONFLICT(tool_name) DO UPDATE SET
                failure_count = excluded.failure_count,
                state = excluded.state,
                last_failure_at = excluded.last_failure_at
            """,
            (tool_name, failure_count, state, now),
        )
        LOGGER.warning(
            "Tool failure recorded: tool=%s, failure_count=%s, state=%s",
            tool_name,
            failure_count,
            state,
        )
        if state == "open":
            LOGGER.error(
                "Loop detected: tool=%s, failure_count=%s, state=OPEN",
                tool_name,
                failure_count,
            )
        return failure_count

    def record_success(self, tool_name: str) -> None:
        now = datetime.now(UTC).isoformat()
        self.database.execute(
            """
            INSERT INTO circuit_breaker_state (
                tool_name, failure_count, state, last_success_at
            ) VALUES (?, 0, 'closed', ?)
            ON CONFLICT(tool_name) DO UPDATE SET
                failure_count = 0,
                state = 'closed',
                last_success_at = excluded.last_success_at
            """,
            (tool_name, now),
        )

    def _set_half_open(self, tool_name: str) -> None:
        self.database.execute(
            "UPDATE circuit_breaker_state SET state = 'half_open' WHERE tool_name = ?",
            (tool_name,),
        )
