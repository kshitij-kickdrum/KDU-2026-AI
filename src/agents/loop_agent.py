from __future__ import annotations

import logging

from src.agents.base_agent import BaseSDKAgent
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
        return self.run("Count the active users")
