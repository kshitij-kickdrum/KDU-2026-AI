from __future__ import annotations

import logging

from src.agents.base_agent import BaseSDKAgent
from src.core.circuit_breaker import FALLBACK_RESPONSE
from src.core.exceptions import CircuitBreakerOpenError
from src.tools.database_tools import create_database_tools
from src.tools.runtime import ToolRuntime
from src.utils.config import AppConfig

LOGGER = logging.getLogger(__name__)


class LoopDetectionAgent(BaseSDKAgent):
    def __init__(self, config: AppConfig, runtime: ToolRuntime, session_id: str) -> None:
        self.runtime = runtime
        self.session_id = session_id
        self.threshold = config.circuit_breaker.threshold
        super().__init__(
            name="LoopDetectionAgent",
            instructions=(
                "You are a loop detection demo agent. Use query_internal_database "
                "when asked to count active users. If the tool cannot be used, explain the failure."
            ),
            model=config.models.reasoning,
            tools=create_database_tools(runtime, session_id),
            config=config,
        )

    def run_circuit_breaker_demo(self) -> str:
        LOGGER.info(
            "Starting circuit breaker demo for query_internal_database with max_failures=%s",
            self.threshold,
        )
        for attempt in range(1, self.threshold + 1):
            try:
                self.runtime.invoke(
                    session_id=self.session_id,
                    agent_name="LoopDetectionAgent",
                    tool_name="query_internal_database",
                    parameters={"attempt": attempt},
                    handler=lambda: (_ for _ in ()).throw(
                        RuntimeError("500 internal database error")
                    ),
                )
            except CircuitBreakerOpenError:
                LOGGER.info("Circuit breaker blocked attempt=%s", attempt)
                return FALLBACK_RESPONSE
            except Exception:
                if self.runtime.circuit_breaker.is_open("query_internal_database"):
                    LOGGER.info("Circuit breaker opened after attempt=%s", attempt)
                    return FALLBACK_RESPONSE
                LOGGER.info("Retrying failing tool after attempt=%s", attempt)
        return FALLBACK_RESPONSE
