from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

MAX_TURNS = 10
SUMMARIZATION_THRESHOLD = 50_000


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def count_tokens(text: str) -> int:
    try:
        import tiktoken

        return len(tiktoken.encoding_for_model("gpt-4o-mini").encode(text))
    except Exception:
        return max(1, len(text.split()))


def prune_message_history(
    messages: list[dict[str, Any]],
    session_id: str | None = None,
    monitor: Any | None = None,
    session_token_count: int = 0,
) -> list[dict[str, Any]]:
    system_prompt = messages[0] if messages and messages[0].get("role") == "system" else None
    history = messages[1:] if system_prompt else list(messages)
    original_len = len(history)
    if len(history) > MAX_TURNS:
        tokens_before = sum(count_tokens(str(m.get("content", ""))) for m in history)
        history = history[-MAX_TURNS:]
        tokens_after = sum(count_tokens(str(m.get("content", ""))) for m in history)
        if monitor and session_id:
            monitor.log_sync(
                {
                    "record_type": "pruning_event",
                    "session_id": session_id,
                    "pruning_type": "truncation",
                    "turns_removed": original_len - MAX_TURNS,
                    "tokens_before": tokens_before,
                    "tokens_after": tokens_after,
                    "timestamp_utc": utcnow_iso(),
                }
            )

    if session_token_count > SUMMARIZATION_THRESHOLD and len(history) >= 5:
        oldest = history[:5]
        summary = " ".join(str(m.get("content", "")) for m in oldest)
        summary = summary[:500]
        tokens_before = sum(count_tokens(str(m.get("content", ""))) for m in oldest)
        history = [{"role": "assistant", "content": f"[Summary]: {summary}"}] + history[5:]
        if monitor and session_id:
            monitor.log_sync(
                {
                    "record_type": "pruning_event",
                    "session_id": session_id,
                    "pruning_type": "summarization",
                    "turns_removed": 5,
                    "tokens_before": tokens_before,
                    "tokens_after": count_tokens(summary),
                    "timestamp_utc": utcnow_iso(),
                }
            )

    return ([system_prompt] + history) if system_prompt else history


@dataclass
class AgentState:
    session_id: str
    intent: str
    transcript: str
    message_history: list[dict[str, Any]]
    timestamp_utc: str = field(default_factory=utcnow_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.message_history = prune_message_history(self.message_history, self.session_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "intent": self.intent,
            "transcript": self.transcript,
            "message_history": self.message_history,
            "timestamp_utc": self.timestamp_utc,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentState":
        return cls(
            session_id=str(data["session_id"]),
            intent=str(data["intent"]),
            transcript=str(data["transcript"]),
            message_history=list(data.get("message_history", [])),
            timestamp_utc=str(data.get("timestamp_utc") or utcnow_iso()),
            metadata=dict(data.get("metadata", {})),
        )

    def append_message(self, role: str, content: str, **extra: Any) -> None:
        message = {"role": role, "content": content}
        message.update(extra)
        self.message_history.append(message)
        self.message_history = prune_message_history(self.message_history, self.session_id)

