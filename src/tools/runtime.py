from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from src.core.circuit_breaker import CircuitBreaker
from src.core.exceptions import CircuitBreakerOpenError
from src.storage.database import Database

LOGGER = logging.getLogger(__name__)


class ToolRuntime:
    def __init__(self, database: Database, circuit_breaker: CircuitBreaker) -> None:
        self.database = database
        self.circuit_breaker = circuit_breaker

    def invoke(
        self,
        *,
        session_id: str,
        agent_name: str,
        tool_name: str,
        parameters: dict[str, Any],
        handler: Callable[[], str],
    ) -> str:
        try:
            self.circuit_breaker.ensure_allowed(tool_name)
            result = handler()
            self.circuit_breaker.record_success(tool_name)
            self.log_invocation(
                session_id=session_id,
                agent_name=agent_name,
                tool_name=tool_name,
                parameters=parameters,
                response_status="success",
                response_data=result,
            )
            return result
        except CircuitBreakerOpenError:
            self.log_invocation(
                session_id=session_id,
                agent_name=agent_name,
                tool_name=tool_name,
                parameters=parameters,
                response_status="error",
                error_message="circuit breaker open",
            )
            raise
        except Exception as exc:
            failure_count = self.circuit_breaker.record_failure(tool_name)
            LOGGER.exception(
                "Tool failed: agent=%s tool=%s failure_count=%s",
                agent_name,
                tool_name,
                failure_count,
            )
            self.log_invocation(
                session_id=session_id,
                agent_name=agent_name,
                tool_name=tool_name,
                parameters=parameters,
                response_status="error",
                error_message=str(exc),
            )
            raise

    def log_invocation(
        self,
        *,
        session_id: str,
        agent_name: str,
        tool_name: str,
        parameters: dict[str, Any],
        response_status: str,
        response_data: str | None = None,
        error_message: str | None = None,
    ) -> None:
        self.database.execute(
            """
            INSERT INTO tool_invocations (
                session_id, agent_name, tool_name, parameters,
                response_status, response_data, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                agent_name,
                tool_name,
                self.database.dumps(parameters),
                response_status,
                response_data,
                error_message,
            ),
        )
