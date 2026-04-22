import time
from typing import Any

import httpx

from app.config import settings
from app.database.models import ToolResult
from app.tools.base import BaseTool


class SearchTool(BaseTool):
    name = "search"
    free_quota_limit = 2500

    def __init__(self) -> None:
        self._queries_used = 0

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": "Search for current information on any topic",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return (1-10)",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            },
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()
        query = str(kwargs.get("query", "")).strip()
        num_results = int(kwargs.get("num_results", 5))
        num_results = max(1, min(10, num_results))
        if not query:
            return ToolResult(success=False, data=None, error_message="query is required")
        if self._queries_used >= self.free_quota_limit:
            return ToolResult(
                success=False,
                data=None,
                error_message="Serper free quota exhausted",
                execution_time=time.perf_counter() - started,
            )
        if not settings.serper_api_key:
            return ToolResult(
                success=False,
                data=None,
                error_message="Serper API key is not configured",
            )

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{settings.serper_base_url}/search",
                    headers={"X-API-KEY": settings.serper_api_key},
                    json={"q": query, "num": num_results},
                )
            self._queries_used += 1
            if response.status_code != 200:
                return ToolResult(
                    success=False,
                    data=None,
                    error_message=f"Search API error {response.status_code}: {response.text[:120]}",
                    execution_time=time.perf_counter() - started,
                )
            payload = response.json()
            organic = payload.get("organic", [])
            results = [
                {
                    "title": item.get("title"),
                    "snippet": item.get("snippet"),
                    "url": item.get("link"),
                }
                for item in organic[:num_results]
            ]
            return ToolResult(
                success=True,
                data={"query": query, "results": results, "quota_used": self._queries_used},
                execution_time=time.perf_counter() - started,
            )
        except httpx.HTTPError as exc:
            return ToolResult(
                success=False,
                data=None,
                error_message=f"Search request failed: {exc}",
                execution_time=time.perf_counter() - started,
            )

