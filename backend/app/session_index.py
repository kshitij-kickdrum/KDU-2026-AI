"""Session discovery index backed by a lightweight JSON file."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any


_INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sessions.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir() -> None:
    index_dir = os.path.dirname(os.path.abspath(_INDEX_PATH))
    if index_dir and not os.path.exists(index_dir):
        os.makedirs(index_dir, exist_ok=True)


def _load_index() -> dict[str, dict[str, Any]]:
    _ensure_dir()
    if not os.path.exists(_INDEX_PATH):
        return {}
    try:
        with open(_INDEX_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
            return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def _save_index(index: dict[str, dict[str, Any]]) -> None:
    _ensure_dir()
    with open(_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)


def _generate_ref() -> str:
    return uuid.uuid4().hex[:12]


def get_or_create_session_ref(thread_id: str) -> str:
    index = _load_index()
    existing = index.get(thread_id)
    if existing and isinstance(existing.get("session_ref"), str):
        return existing["session_ref"]

    session_ref = _generate_ref()
    index[thread_id] = {
        "session_ref": session_ref,
        "thread_id": thread_id,
        "status": "in_progress",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "portfolio_total_usd": None,
        "portfolio_total_converted": None,
        "currency": None,
    }
    _save_index(index)
    return session_ref


def upsert_session(
    *,
    thread_id: str,
    status: str,
    state: dict[str, Any] | None = None,
    cancelled: bool = False,
) -> str:
    index = _load_index()
    existing = index.get(thread_id, {})
    session_ref = existing.get("session_ref") or _generate_ref()
    created_at = existing.get("created_at") or _now_iso()

    state = state or {}
    effective_status = "cancelled" if cancelled else status

    index[thread_id] = {
        "session_ref": session_ref,
        "thread_id": thread_id,
        "status": effective_status,
        "created_at": created_at,
        "updated_at": _now_iso(),
        "portfolio_total_usd": state.get("portfolio_total_usd"),
        "portfolio_total_converted": state.get("portfolio_total_converted"),
        "currency": state.get("currency"),
    }
    _save_index(index)
    return session_ref


def list_sessions(limit: int = 20) -> list[dict[str, Any]]:
    index = _load_index()
    rows = list(index.values())
    rows.sort(key=lambda row: row.get("updated_at", ""), reverse=True)
    return rows[:limit]


def resolve_thread_id(identifier: str) -> str | None:
    """Resolve either raw thread_id or session_ref to a thread_id."""
    index = _load_index()
    if identifier in index:
        return identifier
    for thread_id, row in index.items():
        if row.get("session_ref") == identifier:
            return thread_id
    return None


def resolve_session_ref(identifier: str) -> str:
    index = _load_index()
    row = index.get(identifier)
    if row and isinstance(row.get("session_ref"), str):
        return row["session_ref"]
    return identifier
