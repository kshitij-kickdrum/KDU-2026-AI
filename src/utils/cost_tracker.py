"""Token usage tracking and cost estimation."""

from __future__ import annotations

from dataclasses import dataclass, field

PRICING = {
    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
    "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
    "openai/gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
}


@dataclass
class CostTracker:
    """Track per-agent tokens and estimate USD cost."""

    usage: dict[str, dict[str, int]] = field(default_factory=dict)

    def record_tokens(
        self, agent_role: str, prompt_tokens: int, completion_tokens: int
    ) -> None:
        """Record prompt and completion tokens for an agent role."""
        bucket = self.usage.setdefault(
            agent_role, {"prompt_tokens": 0, "completion_tokens": 0}
        )
        bucket["prompt_tokens"] += prompt_tokens
        bucket["completion_tokens"] += completion_tokens

    def estimate_cost(self, model: str = "gpt-4o-mini") -> float:
        """Estimate total cost in USD."""
        pricing = PRICING.get(model, PRICING["gpt-4o-mini"])
        prompt = sum(v["prompt_tokens"] for v in self.usage.values())
        completion = sum(v["completion_tokens"] for v in self.usage.values())
        return round(
            (prompt / 1000) * pricing["prompt"]
            + (completion / 1000) * pricing["completion"],
            6,
        )

    def get_summary(self) -> dict[str, object]:
        """Return token totals, per-agent usage, and estimated cost."""
        prompt = sum(v["prompt_tokens"] for v in self.usage.values())
        completion = sum(v["completion_tokens"] for v in self.usage.values())
        return {
            "total_tokens": prompt + completion,
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "per_agent": self.usage,
            "estimated_usd": self.estimate_cost(),
        }
