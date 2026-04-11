from fastapi import APIRouter

from app.memory.session_memory import get_history
from app.models.response_models import HistoryMessage, HistoryResponse

router = APIRouter()


@router.get("/history", response_model=HistoryResponse)
async def history(session_id: str, user_id: str) -> HistoryResponse:
    messages = get_history(session_id)
    return HistoryResponse(
        session_id=session_id,
        message_count=len(messages),
        messages=[HistoryMessage(**m) for m in messages],
    )
