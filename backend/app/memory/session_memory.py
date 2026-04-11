import json
import time

from app.core.logging import get_logger

logger = get_logger(__name__)

_store: dict[str, list[dict]] = {}
_session_owner: dict[str, str] = {}
_session_index: dict[str, list[dict]] = {}


def _now_ms() -> int:
    return int(time.time() * 1000)


def _normalize_text(value: str) -> str:
    return " ".join(value.split()).strip()


def _truncate_text(value: str, limit: int) -> str:
    return f"{value[: limit - 3].rstrip()}..." if len(value) > limit else value


def _build_title(human_msg: str) -> str:
    normalized = _normalize_text(human_msg)
    if not normalized:
        return "New chat"
    if normalized.lower() == "describe this image":
        return "Image analysis"
    return _truncate_text(normalized, 38)


def _serialize_ai_content(ai_content: str | dict) -> str:
    if isinstance(ai_content, dict):
        return json.dumps(ai_content, ensure_ascii=False)
    return ai_content


def _build_preview(ai_content: str | dict, human_msg: str) -> str:
    if isinstance(ai_content, dict):
        parsed = ai_content
    else:
        try:
            parsed = json.loads(ai_content)
        except json.JSONDecodeError:
            parsed = None

    if isinstance(parsed, dict):
        if {"temperature", "summary"}.issubset(parsed):
            return _truncate_text(
                _normalize_text(f"{parsed['temperature']} - {parsed['summary']}"),
                56,
            )
        if "description" in parsed:
            return _truncate_text(_normalize_text(str(parsed["description"])), 56)
        if "answer" in parsed:
            return _truncate_text(_normalize_text(str(parsed["answer"])), 56)

    fallback_source = ai_content if isinstance(ai_content, str) else human_msg
    fallback = _normalize_text(fallback_source or human_msg)
    return _truncate_text(fallback, 56)


def _upsert_session_summary(user_id: str, session_id: str, human_msg: str, ai_content: str | dict) -> None:
    sessions = _session_index.setdefault(user_id, [])
    existing = next((item for item in sessions if item["session_id"] == session_id), None)
    timestamp = _now_ms()

    if existing is None:
        sessions.append({
            "session_id": session_id,
            "title": _build_title(human_msg),
            "preview": _build_preview(ai_content, human_msg),
            "created_at": timestamp,
            "updated_at": timestamp,
            "message_count": 2,
        })
    else:
        existing["preview"] = _build_preview(ai_content, human_msg)
        existing["updated_at"] = timestamp
        existing["message_count"] = len(_store.get(session_id, []))

    sessions.sort(key=lambda item: item["updated_at"], reverse=True)


def create_session(session_id: str, user_id: str, title: str = "New chat") -> None:
    sessions = _session_index.setdefault(user_id, [])
    existing = next((item for item in sessions if item["session_id"] == session_id), None)

    if existing is not None:
        existing["updated_at"] = _now_ms()
        sessions.sort(key=lambda item: item["updated_at"], reverse=True)
        return

    timestamp = _now_ms()
    _store.setdefault(session_id, [])
    _session_owner[session_id] = user_id
    sessions.append({
        "session_id": session_id,
        "title": title,
        "preview": "",
        "created_at": timestamp,
        "updated_at": timestamp,
        "message_count": 0,
    })
    sessions.sort(key=lambda item: item["updated_at"], reverse=True)


def add_turn(session_id: str, user_id: str, human_msg: str, ai_content: str | dict) -> None:
    if session_id not in _store:
        _store[session_id] = []

    serialized_ai_content = _serialize_ai_content(ai_content)
    _store[session_id].append({"role": "human", "content": human_msg})
    _store[session_id].append({"role": "ai", "content": serialized_ai_content})
    _session_owner[session_id] = user_id
    _upsert_session_summary(user_id, session_id, human_msg, ai_content)

    logger.info("memory updated", session_id=session_id, total_messages=len(_store[session_id]))


def get_history(session_id: str) -> list[dict]:
    return _store.get(session_id, [])


def list_sessions(user_id: str) -> list[dict]:
    return list(_session_index.get(user_id, []))


def clear_session(session_id: str) -> None:
    if session_id in _store:
        del _store[session_id]

    owner = _session_owner.pop(session_id, None)
    if owner is not None and owner in _session_index:
        _session_index[owner] = [
            item for item in _session_index[owner]
            if item["session_id"] != session_id
        ]

    try:
        from app.agent.agent import _memory
        if session_id in _memory.storage:
            del _memory.storage[session_id]
    except Exception:
        pass

    logger.info("session cleared", session_id=session_id)
