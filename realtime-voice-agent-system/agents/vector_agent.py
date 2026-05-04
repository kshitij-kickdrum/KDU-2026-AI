from __future__ import annotations

import asyncio
import time

from agents.db_agent import AgentResult
from concurrency.queue_manager import ConcurrencyQueue, ConcurrencyTimeoutError
from monitoring.monitor import Monitor
from storage.faiss_store import FAISSStore


class VectorAgent:
    agent_name = "vector_agent"

    def __init__(
        self,
        store: FAISSStore,
        queue: ConcurrencyQueue | None = None,
        monitor: Monitor | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.store = store
        self.queue = queue or ConcurrencyQueue(10, 5)
        self.monitor = monitor
        self.timeout_seconds = timeout_seconds

    async def search(self, question: str, session_id: str) -> AgentResult:
        start = time.perf_counter()
        status = "success"
        data = None
        error = None
        try:
            async with self.queue.acquire():
                results = await asyncio.wait_for(
                    asyncio.to_thread(self.store.search, question, 5),
                    timeout=self.timeout_seconds,
                )
                data = {"matches": results}
        except ConcurrencyTimeoutError as exc:
            status = "timeout"
            error = str(exc)
        except Exception as exc:
            status = "failure"
            error = str(exc)
        latency = int((time.perf_counter() - start) * 1000)
        if self.monitor:
            await self.monitor.log(
                {
                    "record_type": "tool_invocation",
                    "session_id": session_id,
                    "agent_name": self.agent_name,
                    "tool_name": "faiss_search",
                    "input_summary": question[:200],
                    "output_summary": (str(data) if data is not None else str(error))[:200],
                    "latency_ms": latency,
                    "status": status,
                }
            )
        return AgentResult(session_id, self.agent_name, status, data, error, latency)

