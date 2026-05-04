from __future__ import annotations

import asyncio
from dataclasses import dataclass

from agents.consensus_agent import ConsensusAgent
from agents.db_agent import AgentResult, DBAgent
from agents.vector_agent import VectorAgent
from monitoring.monitor import Monitor


@dataclass
class CoordinatorResult:
    session_id: str
    response: str
    db_agent_status: str
    vector_agent_status: str
    error: str | None


class Coordinator:
    def __init__(
        self,
        db_agent: DBAgent,
        vector_agent: VectorAgent,
        consensus_agent: ConsensusAgent,
        monitor: Monitor | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.db_agent = db_agent
        self.vector_agent = vector_agent
        self.consensus_agent = consensus_agent
        self.monitor = monitor
        self.timeout_seconds = timeout_seconds

    async def run(self, query: str, session_id: str) -> CoordinatorResult:
        db_task = asyncio.create_task(self.db_agent.query(query, session_id))
        vector_task = asyncio.create_task(self.vector_agent.search(query, session_id))
        db_result, vector_result = await asyncio.gather(
            self._with_timeout(db_task, session_id, "db_agent"),
            self._with_timeout(vector_task, session_id, "vector_agent"),
        )
        if db_result.status != "success" and vector_result.status != "success":
            error = "both_worker_agents_failed"
            if self.monitor:
                await self.monitor.log(
                    {
                        "record_type": "coordinator_error",
                        "session_id": session_id,
                        "status": "error",
                        "error": error,
                    }
                )
            return CoordinatorResult(
                session_id,
                "I could not reach the billing database or knowledge base right now.",
                db_result.status,
                vector_result.status,
                error,
            )
        response = await self.consensus_agent.aggregate(db_result, vector_result, session_id)
        return CoordinatorResult(
            session_id,
            response,
            db_result.status,
            vector_result.status,
            None,
        )

    async def _with_timeout(
        self, task: asyncio.Task[AgentResult], session_id: str, agent_name: str
    ) -> AgentResult:
        try:
            return await asyncio.wait_for(task, timeout=self.timeout_seconds)
        except asyncio.TimeoutError:
            task.cancel()
            return AgentResult(session_id, agent_name, "timeout", None, "agent_timeout", self.timeout_seconds * 1000)
        except Exception as exc:
            return AgentResult(session_id, agent_name, "failure", None, str(exc), 0)

