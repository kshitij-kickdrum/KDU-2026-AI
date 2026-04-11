from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.requests import Request

from app.core.config import settings
from app.core.limiter import limiter
from app.models.response_models import ChatResponse
from app.services.image_service import handle_image

router = APIRouter()


@router.post("/image")
@limiter.limit(
    settings.image_rate_limit,
    exempt_when=lambda: not settings.enable_rate_limiting,
)
async def image(
    request: Request,
    user_id: Annotated[str, Form()],
    session_id: Annotated[str, Form()],
    image: Annotated[UploadFile, File()],
    style: Annotated[str | None, Form()] = None,
    prompt: Annotated[str | None, Form()] = None,
) -> ChatResponse:
    image_bytes = await image.read()

    result = handle_image(
        session_id=session_id,
        user_id=user_id,
        image_bytes=image_bytes,
        content_type=image.content_type,
        style=style,
        prompt=prompt,
    )
    return ChatResponse(**result)
