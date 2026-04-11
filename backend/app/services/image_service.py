import base64

from langchain_core.messages import HumanMessage
from openai import APIConnectionError, APIStatusError, RateLimitError

from app.core.config import settings
from app.core.exceptions import (
    ImageTooLarge,
    UnsupportedImageFormat,
    UpstreamRateLimited,
    UpstreamServiceUnavailable,
)
from app.core.llm import build_chat_model
from app.core.logging import get_logger
from app.parsers.image_parser import parser as image_parser
from app.parsers.retry import parse_with_retry
from app.memory.session_memory import add_turn
from app.services.postprocessor import build_response

logger = get_logger(__name__)

_ACCEPTED_FORMATS = {"image/jpeg", "image/png", "image/webp"}
_MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

_DEFAULT_PROMPT = (
    "Analyse this image. Respond with valid JSON only, following this schema:\n"
    "{format_instructions}"
)

_vision_llm = build_chat_model(
    model=settings.vision_model,
    api_key=settings.vision_model_api_key,
)


def _build_mock_image_response(prompt: str | None) -> dict:
    request_summary = prompt.strip() if prompt and prompt.strip() else "Describe this image"
    return {
        "description": (
            "Development fallback: the image was received, but the vision provider is unavailable right now. "
            f"Requested prompt: {request_summary}."
        ),
        "objects_detected": ["image"],
        "scene_type": "unknown",
        "confidence": "low",
    }


def _validate(content_type: str, size: int) -> None:
    if content_type not in _ACCEPTED_FORMATS:
        raise UnsupportedImageFormat()
    if size > _MAX_SIZE_BYTES:
        raise ImageTooLarge()


def _encode(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def handle_image(
    session_id: str,
    user_id: str,
    image_bytes: bytes,
    content_type: str,
    style: str | None,
    prompt: str | None,
) -> dict:
    _validate(content_type, len(image_bytes))

    b64 = _encode(image_bytes)
    user_prompt = prompt or _DEFAULT_PROMPT.format(
        format_instructions=image_parser.get_format_instructions()
    )

    logger.info("image_service processing image", session_id=session_id, content_type=content_type)

    message = HumanMessage(content=[
        {"type": "text", "text": user_prompt},
        {"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{b64}"}},
    ])

    try:
        response = _vision_llm.invoke([message])
    except RateLimitError as exc:
        logger.warning(
            "image_service upstream rate limited",
            error_type=type(exc).__name__,
            session_id=session_id,
        )
        if settings.use_mock_model_fallbacks:
            logger.info("image_service using mock fallback after upstream rate limit", session_id=session_id)
            parsed = _build_mock_image_response(prompt)
            human_prompt = prompt or "Describe this image"
            add_turn(session_id, user_id, human_prompt, parsed)
            return build_response(
                session_id=session_id,
                parsed=parsed,
                model_used="fallback-vision",
                tool_used=None,
                style_applied=style,
            )
        raise UpstreamRateLimited() from exc
    except APIStatusError as exc:
        logger.warning(
            "image_service upstream API error",
            error_type=type(exc).__name__,
            status_code=getattr(exc, "status_code", None),
            session_id=session_id,
        )
        if settings.use_mock_model_fallbacks:
            logger.info("image_service using mock fallback after upstream API error", session_id=session_id)
            parsed = _build_mock_image_response(prompt)
            human_prompt = prompt or "Describe this image"
            add_turn(session_id, user_id, human_prompt, parsed)
            return build_response(
                session_id=session_id,
                parsed=parsed,
                model_used="fallback-vision",
                tool_used=None,
                style_applied=style,
            )
        raise UpstreamServiceUnavailable() from exc
    except APIConnectionError as exc:
        logger.warning(
            "image_service upstream connection error",
            error_type=type(exc).__name__,
            session_id=session_id,
        )
        if settings.use_mock_model_fallbacks:
            logger.info("image_service using mock fallback after upstream connection error", session_id=session_id)
            parsed = _build_mock_image_response(prompt)
            human_prompt = prompt or "Describe this image"
            add_turn(session_id, user_id, human_prompt, parsed)
            return build_response(
                session_id=session_id,
                parsed=parsed,
                model_used="fallback-vision",
                tool_used=None,
                style_applied=style,
            )
        raise UpstreamServiceUnavailable() from exc

    parsed = parse_with_retry(response.content, image_parser)
    human_prompt = prompt or "Describe this image"
    add_turn(session_id, user_id, human_prompt, parsed)

    return build_response(
        session_id=session_id,
        parsed=parsed,
        model_used=settings.vision_model,
        tool_used=None,
        style_applied=style,
    )
