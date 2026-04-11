from fastapi import APIRouter
from fastapi.requests import Request

from app.core.config import settings
from app.core.limiter import limiter
from app.models.request_models import ChatRequest
from app.models.response_models import ChatResponse
from app.services.chat_service import handle_chat

router = APIRouter()


@router.post("/chat")
@limiter.limit(
    settings.chat_rate_limit,
    exempt_when=lambda: not settings.enable_rate_limiting,
)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    result = handle_chat(
        user_id=body.user_id,
        session_id=body.session_id,
        message=body.message,
        style_override=body.style,
    )
    return ChatResponse(**result)
