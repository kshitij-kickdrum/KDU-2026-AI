"""Deterministic LLM doubles."""

from __future__ import annotations


class MockLLM:
    """Return canned responses by role."""

    def __init__(self, fact_statuses: list[str] | None = None) -> None:
        self.fact_statuses = fact_statuses or ["passed"]
        self.fact_calls = 0

    def invoke_for_role(self, role: str, task: str) -> str:
        """Return a role-specific response."""
        if role == "researcher":
            return "Research findings with source notes."
        if role == "fact_checker":
            status = self.fact_statuses[
                min(self.fact_calls, len(self.fact_statuses) - 1)
            ]
            self.fact_calls += 1
            return f"{status}: credibility notes."
        if role == "writer":
            return "Executive summary\n\nPolished research document."
        return task


class MockLLMAlwaysFail:
    """Always fail."""

    def invoke_for_role(self, role: str, task: str) -> str:
        """Raise an unavailable error."""
        raise Exception("LLM unavailable")
