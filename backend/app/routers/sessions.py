"""Session discovery endpoints using opaque session refs."""

from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.agent.graph import graph
from app.main import AppException
from app.models import SessionStateResponse, SessionsResponse, SessionSummary
from app.session_index import list_sessions, resolve_thread_id, resolve_session_ref


router = APIRouter()


@router.get("/sessions", response_model=SessionsResponse)
async def get_sessions(limit: Annotated[int, Query(ge=1, le=100)] = 20):
    rows = list_sessions(limit=limit)
    sessions = [
        SessionSummary(
            session_ref=row["session_ref"],
            status=row.get("status", "in_progress"),
            updated_at=row.get("updated_at", ""),
            portfolio_total_usd=row.get("portfolio_total_usd"),
            portfolio_total_converted=row.get("portfolio_total_converted"),
            currency=row.get("currency"),
        )
        for row in rows
    ]
    return SessionsResponse(sessions=sessions)


@router.get("/sessions/{session_ref}", response_model=SessionStateResponse)
async def get_session_state(
    session_ref: Annotated[str, Path(description="Opaque session reference")],
):
    thread_id = resolve_thread_id(session_ref)
    if not thread_id:
        raise AppException(
            code="SESSION_NOT_FOUND",
            message=f"No session found for reference: {session_ref}",
            http_status=404,
        )

    config = {"configurable": {"thread_id": thread_id}}
    state_snapshot = graph.get_state(config)
    if not state_snapshot or not state_snapshot.values:
        raise AppException(
            code="SESSION_NOT_FOUND",
            message=f"No checkpoint found for session reference: {session_ref}",
            http_status=404,
        )

    current_state = state_snapshot.values
    pending_action = current_state.get("pending_action")
    action_approved = bool(current_state.get("action_approved"))

    if pending_action in {"buy", "sell"} and not action_approved:
        status = "awaiting_approval"
    elif not state_snapshot.next:
        status = "completed"
    else:
        status = "in_progress"

    return SessionStateResponse(
        session_ref=resolve_session_ref(thread_id),
        status=status,
        state=current_state,
    )
