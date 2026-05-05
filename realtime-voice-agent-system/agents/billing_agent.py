from __future__ import annotations

import asyncio
import re
import time
from collections.abc import AsyncIterator

from agents.base_agent import BaseAgent, trim_words
from state.agent_state import AgentState
from tts.kokoro_tts import TTSEngine


FALLBACK_RESPONSE = (
    "I can help with billing, but I could not reach the language model right now. "
    "Please check your account ID, invoice, or payment question and try again."
)


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
            text = FALLBACK_RESPONSE
        state.append_message("assistant", text)
        return text

    async def stream_response_sentences(
        self, state: AgentState
    ) -> AsyncIterator[str]:
        if self.llm_client is None:
            state.append_message("assistant", FALLBACK_RESPONSE)
            yield FALLBACK_RESPONSE
            return

        messages = [
            {
                "role": "system",
                "content": "You are a billing support agent. Answer in 80 words or fewer.",
            },
            {"role": "user", "content": state.transcript},
        ]
        start = time.perf_counter()
        status = "success"
        error: str | None = None
        generated_parts: list[str] = []
        buffer = ""
        yielded_any = False
        try:
            async for delta in self.llm_client.stream_complete(messages, self.model):
                generated_parts.append(delta)
                buffer += delta
                sentences, buffer = _split_complete_sentences(buffer)
                for sentence in sentences:
                    text = sentence.strip()
                    if text:
                        yielded_any = True
                        yield text
            tail = buffer.strip()
            if tail:
                yielded_any = True
                yield tail
            if not yielded_any:
                status = "error"
                error = "empty_stream"
                yield FALLBACK_RESPONSE
        except asyncio.CancelledError:
            status = "interrupted"
            raise
        except Exception as exc:
            status = "error"
            error = str(exc)
            generated_parts = [FALLBACK_RESPONSE]
            yield FALLBACK_RESPONSE
        finally:
            generated_text = trim_words("".join(generated_parts).strip(), 150)
            if generated_text:
                state.append_message("assistant", generated_text)
            if self.monitor:
                await self.monitor.log(
                    {
                        "record_type": "llm_call",
                        "session_id": state.session_id,
                        "agent_name": self.agent_name,
                        "model_id": self.model,
                        "prompt_tokens": 0,
                        "completion_tokens": len(generated_text.split()),
                        "latency_ms": int((time.perf_counter() - start) * 1000),
                        "status": status,
                        "error": error,
                        "streaming": True,
                    }
                )

    def mark_truncated(self, state: AgentState, unspoken_text: str) -> None:
        if state.message_history:
            state.message_history[-1]["truncated"] = True
            state.message_history[-1]["unspoken_chars"] = len(unspoken_text)


def _split_complete_sentences(text: str) -> tuple[list[str], str]:
    matches = list(re.finditer(r"(?<=[.!?\n])\s+", text))
    if not matches:
        return [], text
    last = matches[-1].end()
    complete = text[:last]
    remainder = text[last:]
    sentences = [part for part in re.split(r"(?<=[.!?\n])\s+", complete) if part.strip()]
    return sentences, remainder
