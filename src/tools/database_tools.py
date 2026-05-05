from __future__ import annotations

from typing import Any

from src.agents.sdk import load_agents_sdk
from src.tools.runtime import ToolRuntime


def create_database_tools(runtime: ToolRuntime, session_id: str) -> list[Any]:
    _, _, function_tool, _ = load_agents_sdk()

    @function_tool
    def query_internal_database() -> str:
        """Count active users by querying the internal database."""
        return runtime.invoke(
            session_id=session_id,
            agent_name="LoopDetectionAgent",
            tool_name="query_internal_database",
            parameters={},
            handler=lambda: (_ for _ in ()).throw(RuntimeError("500 internal database error")),
        )

    return [query_internal_database]
