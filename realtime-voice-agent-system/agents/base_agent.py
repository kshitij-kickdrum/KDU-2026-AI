from __future__ import annotations

from monitoring.monitor import Monitor
from llm.llm_client import LLMClient, LLMResponse


class BaseAgent:
    agent_name = "base_agent"

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        monitor: Monitor | None = None,
        model: str = "gpt-4o-mini",
    ) -> None:
        self.llm_client = llm_client
        self.monitor = monitor
        self.model = model

    async def complete(self, session_id: str, messages: list[dict[str, str]]) -> LLMResponse:
        if self.llm_client is None:
            return LLMResponse("", self.model, 0, 0, 0, "error", "no_llm_client")
        response = await self.llm_client.complete(messages, self.model)
        if self.monitor:
            await self.monitor.log(
                {
                    "record_type": "llm_call",
                    "session_id": session_id,
                    "agent_name": self.agent_name,
                    "model_id": response.model_id,
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                    "latency_ms": response.latency_ms,
                    "status": response.status,
                    "error": response.error,
                }
            )
        return response


def trim_words(text: str, max_words: int) -> str:
    words = text.split()
    return " ".join(words[:max_words])

