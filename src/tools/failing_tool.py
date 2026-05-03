"""Custom CrewAI tool that raises TimeoutError with 50% probability."""

from __future__ import annotations

import random

try:
    from crewai.tools import BaseTool
except Exception:  # pragma: no cover
    from pydantic import BaseModel

    class BaseTool(BaseModel):  # type: ignore[no-redef]
        """Minimal fallback when CrewAI is unavailable."""

        name: str = ""
        description: str = ""


class UnreliableResearchTool(BaseTool):
    """Intermittently failing supplemental research tool."""

    name: str = "unreliable_research_tool"
    description: str = "Returns supplemental data or simulates a timeout."

    def _run(self, query: str) -> str:
        """Run the tool for a 1-500 character query."""
        if not isinstance(query, str) or not 1 <= len(query) <= 500:
            raise ValueError("query: expected str with length 1-500")
        if random.random() < 0.5:
            raise TimeoutError("Simulated tool timeout")
        return f"Supplemental data for: {query}"
