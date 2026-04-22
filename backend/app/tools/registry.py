from collections.abc import Iterable
from typing import Any

from app.database.models import ToolResult
from app.tools.base import BaseTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register_tool(self, tool: BaseTool) -> None:
        schema = tool.schema
        if "function" not in schema or "name" not in schema["function"]:
            raise ValueError("Invalid tool schema")
        self._tools[tool.name] = tool

    def register_many(self, tools: Iterable[BaseTool]) -> None:
        for tool in tools:
            self.register_tool(tool)

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        return [tool.schema for tool in self._tools.values()]

    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self._tools

    async def execute_tool(self, tool_name: str, parameters: dict[str, Any]) -> ToolResult:
        tool = self._tools.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                data=None,
                error_message=f"Tool '{tool_name}' is not registered",
            )
        try:
            return await tool.execute(**parameters)
        except Exception as exc:  # pragma: no cover - defensive
            return ToolResult(
                success=False,
                data=None,
                error_message=f"{tool_name} execution failed: {exc}",
            )

