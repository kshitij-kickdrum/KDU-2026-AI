from __future__ import annotations

from agents.base_agent import BaseAgent, trim_words
from state.agent_state import AgentState
from tts.kokoro_tts import TTSEngine


class BillingAgent(BaseAgent):
    agent_name = "billing_agent"

    def __init__(self, *args, tts_engine: TTSEngine | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.tts_engine = tts_engine

    async def respond(self, state: AgentState) -> str:
        response = await self.complete(
            state.session_id,
            [
                {
                    "role": "system",
                    "content": "You are a billing support agent. Answer in 150 words or fewer.",
                },
                {"role": "user", "content": state.transcript},
            ],
        )
        if response.status == "success" and response.content.strip():
            text = trim_words(response.content.strip(), 150)
        else:
            text = "I can help with billing, but I could not reach the language model right now. Please check your account ID, invoice, or payment question and try again."
        state.append_message("assistant", text)
        return text

    def mark_truncated(self, state: AgentState, unspoken_text: str) -> None:
        if state.message_history:
            state.message_history[-1]["truncated"] = True
            state.message_history[-1]["unspoken_chars"] = len(unspoken_text)

