from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID


class InMemorySessionStore:
    def __init__(self, ttl_minutes: int = 60) -> None:
        self._store: dict[UUID, dict[str, Any]] = {}
        self._ttl = timedelta(minutes=ttl_minutes)

    def create_or_update(self, session_id: UUID, payload: dict[str, Any]) -> None:
        self._store[session_id] = {
            **self._store.get(session_id, {}),
            **payload,
            "updated_at": datetime.now(timezone.utc),
        }

    def get(self, session_id: UUID) -> dict[str, Any] | None:
        item = self._store.get(session_id)
        if not item:
            return None
        updated_at: datetime = item.get("updated_at", datetime.now(timezone.utc))
        if datetime.now(timezone.utc) - updated_at > self._ttl:
            self._store.pop(session_id, None)
            return None
        return item

    def cleanup(self) -> int:
        now = datetime.now(timezone.utc)
        expired = [sid for sid, item in self._store.items() if now - item.get("updated_at", now) > self._ttl]
        for sid in expired:
            self._store.pop(sid, None)
        return len(expired)
