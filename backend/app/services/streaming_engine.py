import json
from collections.abc import AsyncGenerator

from app.database.models import ToolResult


class StreamingEngine:
    def __init__(self) -> None:
        self._cache: dict[str, str] = {}

    async def stream_response(
        self,
        session_id: str,
        text_stream: AsyncGenerator[str, None],
        used_tools: list[str],
        tool_results: list[ToolResult],
        usage: dict,
    ) -> AsyncGenerator[str, None]:
        for name in used_tools:
            payload = {"type": "tool_status", "data": {"tool": name, "status": "executing"}}
            yield self._sse(payload)

        for name, result in zip(used_tools, tool_results, strict=False):
            payload = {
                "type": "tool_result",
                "data": {
                    "tool": name,
                    "success": result.success,
                    "data": result.data,
                    "error": result.error_message,
                },
            }
            yield self._sse(payload)

        content_buffer = ""
        async for chunk in text_stream:
            content_buffer += chunk
            self._cache[session_id] = content_buffer
            yield self._sse({"type": "content", "data": chunk})

        yield self._sse({"type": "usage_update", "data": usage})
        yield self._sse({"type": "done", "data": {"complete": True}})

    def get_cached_response(self, session_id: str) -> str | None:
        return self._cache.get(session_id)

    @staticmethod
    def _sse(payload: dict) -> str:
        return f"data: {json.dumps(payload)}\n\n"

