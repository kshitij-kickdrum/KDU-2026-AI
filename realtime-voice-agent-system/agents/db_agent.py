from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass
from typing import Any

from concurrency.queue_manager import ConcurrencyQueue, ConcurrencyTimeoutError
from monitoring.monitor import Monitor
from storage.sqlite_store import SQLiteStore


@dataclass
class AgentResult:
    session_id: str
    agent_name: str
    status: str
    data: dict[str, Any] | None
    error: str | None
    latency_ms: int


class DBAgent:
    agent_name = "db_agent"

    def __init__(
        self,
        store: SQLiteStore,
        queue: ConcurrencyQueue | None = None,
        monitor: Monitor | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.store = store
        self.queue = queue or ConcurrencyQueue(5, 5)
        self.monitor = monitor
        self.timeout_seconds = timeout_seconds

    async def query(self, question: str, session_id: str) -> AgentResult:
        start = time.perf_counter()
        status = "success"
        data: dict[str, Any] | None = None
        error = None
        try:
            async with self.queue.acquire():
                rows = await asyncio.wait_for(
                    asyncio.to_thread(self.store.find_customer, _extract_lookup(question)),
                    timeout=self.timeout_seconds,
                )
                data = {"rows": rows}
        except ConcurrencyTimeoutError as exc:
            status = "timeout"
            error = str(exc)
        except Exception as exc:
            status = "failure"
            error = "database_unavailable"
        latency = int((time.perf_counter() - start) * 1000)
        await self._log(session_id, question, data, status, latency, error)
        return AgentResult(session_id, self.agent_name, status, data, error, latency)

    async def _log(
        self,
        session_id: str,
        question: str,
        data: dict[str, Any] | None,
        status: str,
        latency_ms: int,
        error: str | None,
    ) -> None:
        if self.monitor:
            await self.monitor.log(
                {
                    "record_type": "tool_invocation",
                    "session_id": session_id,
                    "agent_name": self.agent_name,
                    "tool_name": "sqlite_query",
                    "input_summary": question[:200],
                    "output_summary": (str(data) if data is not None else str(error))[:200],
                    "latency_ms": latency_ms,
                    "status": status,
                }
            )


def _extract_lookup(question: str) -> str:
    customer_id = re.search(r"\bC-\d+\b", question, flags=re.IGNORECASE)
    if customer_id:
        return customer_id.group(0).upper()
    email = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", question)
    if email:
        return email.group(0)
    return question.strip()
