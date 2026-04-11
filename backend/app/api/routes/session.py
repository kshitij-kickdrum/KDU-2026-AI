from fastapi import APIRouter

from app.memory.session_memory import clear_session, create_session, list_sessions
from app.models.request_models import SessionRequest
from app.models.response_models import SessionListResponse, SessionSummary

router = APIRouter()


@router.get("/sessions", response_model=SessionListResponse)
async def get_sessions(user_id: str) -> SessionListResponse:
    sessions = [
        SessionSummary(**session)
        for session in list_sessions(user_id)
    ]
    return SessionListResponse(sessions=sessions)


@router.post("/session")
async def create_new_session(request: SessionRequest) -> dict:
    create_session(request.session_id, request.user_id)
    return {"message": f"Session {request.session_id} created."}


@router.delete("/session")
async def delete_session(request: SessionRequest) -> dict:
    clear_session(request.session_id)
    return {"message": f"Session {request.session_id} cleared."}
