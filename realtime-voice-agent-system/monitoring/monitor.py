from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from state.agent_state import utcnow_iso


SENSITIVE_KEY_NAMES = {
    "authorization",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "bearer",
}
SENSITIVE_KEY_SUFFIXES = ("_api_key", "-api-key")


def redact_credentials(value: Any) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text in SENSITIVE_KEY_NAMES or key_text.endswith(SENSITIVE_KEY_SUFFIXES):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_credentials(item)
        return redacted
    if isinstance(value, list):
        return [redact_credentials(item) for item in value]
    if isinstance(value, str) and value.lower().startswith("bearer "):
        return "Bearer [REDACTED]"
    return value


class Monitor:
    def __init__(self, log_path: str | Path = "logs/session.ndjson") -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    async def log(self, event: dict[str, Any]) -> None:
        record = redact_credentials(dict(event))
        record.setdefault("timestamp_utc", utcnow_iso())
        line = json.dumps(record, ensure_ascii=False) + "\n"
        try:
            async with self._lock:
                await asyncio.to_thread(self._append_line, line)
        except OSError as exc:
            print(f"[Monitor] Log write failed: {exc} | Record: {line}", file=sys.stderr)

    def log_sync(self, event: dict[str, Any]) -> None:
        record = redact_credentials(dict(event))
        record.setdefault("timestamp_utc", utcnow_iso())
        line = json.dumps(record, ensure_ascii=False) + "\n"
        try:
            self._append_line(line)
        except OSError as exc:
            print(f"[Monitor] Log write failed: {exc} | Record: {line}", file=sys.stderr)

    def replay(self, session_id: str) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []
        events = []
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("session_id") == session_id:
                events.append(record)
        return sorted(events, key=lambda item: item.get("timestamp_utc", ""))

    def _append_line(self, line: str) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line)
