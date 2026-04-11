import re

from openai import APIConnectionError, APIStatusError, RateLimitError

from app.agent.agent import build_agent, run_agent
from app.agent.router import classify_intent
from app.core.config import settings
from app.core.exceptions import UpstreamRateLimited, UpstreamServiceUnavailable
from app.core.logging import get_logger
from app.memory.session_memory import add_turn
from app.parsers.chat_parser import parser as chat_parser
from app.parsers.retry import parse_with_retry
from app.parsers.weather_parser import parser as weather_parser
from app.prompts.system_prompt import build_system_prompt
from app.security.sanitizer import sanitize_input
from app.services.postprocessor import build_response
from app.services.user_service import get_user_profile
from app.tools.weather_tool import get_weather

logger = get_logger(__name__)

_LOCATION_PATTERNS = (
    re.compile(r"\b(?:weather|temperature|forecast)(?:\s+\w+){0,3}?\s+(?:in|at|for|of)\s+(.+)$", re.IGNORECASE),
    re.compile(r"\b(?:in|at|for)\s+(.+)$", re.IGNORECASE),
)

_TRAILING_LOCATION_NOISE = re.compile(
    r"(?:\b(?:today|tomorrow|now|right now|currently|please)\b|[?.!,])+$",
    re.IGNORECASE,
)


def _extract_weather_location(message: str) -> str | None:
    cleaned = message.strip()

    for pattern in _LOCATION_PATTERNS:
        match = pattern.search(cleaned)
        if not match:
            continue

        location = match.group(1).strip(" \t\n\r,.?!")
        location = _TRAILING_LOCATION_NOISE.sub("", location).strip(" \t\n\r,.?!")

        if location:
            return location

    return None


def _resolve_weather_location(message: str, profile: dict) -> str:
    explicit_location = _extract_weather_location(message)
    if explicit_location:
        logger.info("chat_service weather location override", location=explicit_location)
        return explicit_location
    return profile.get("location", "")


def _build_mock_chat_response(message: str, style: str) -> dict:
    normalized = " ".join(message.split())
    if style == "child":
        return {
            "answer": (
                f"I got your message: '{normalized}'. The AI service is busy, so this is a simple backup reply."
            ),
            "follow_up": "Try again in a little while and I can give a smarter answer.",
        }

    return {
        "answer": (
            f"Development fallback response for: '{normalized}'. The upstream AI provider is currently unavailable."
        ),
        "follow_up": "Retry shortly to get the full model-generated response.",
    }


def _run_text_agent(message: str, session_id: str, profile: dict, style: str) -> tuple[dict, str | None, str]:
    system_prompt = build_system_prompt(profile, style, intent="chat")
    agent = build_agent(system_prompt, enable_tools=False)

    try:
        raw_output, tool_used = run_agent(agent, message, session_id)
    except RateLimitError as exc:
        logger.warning(
            "chat_service upstream rate limited",
            error_type=type(exc).__name__,
            session_id=session_id,
        )
        if settings.use_mock_model_fallbacks:
            logger.info("chat_service using mock fallback after upstream rate limit", session_id=session_id)
            return _build_mock_chat_response(message, style), None, "fallback-chat"
        raise UpstreamRateLimited() from exc
    except APIStatusError as exc:
        logger.warning(
            "chat_service upstream API error",
            error_type=type(exc).__name__,
            status_code=getattr(exc, "status_code", None),
            session_id=session_id,
        )
        if settings.use_mock_model_fallbacks:
            logger.info("chat_service using mock fallback after upstream API error", session_id=session_id)
            return _build_mock_chat_response(message, style), None, "fallback-chat"
        raise UpstreamServiceUnavailable() from exc
    except APIConnectionError as exc:
        logger.warning(
            "chat_service upstream connection error",
            error_type=type(exc).__name__,
            session_id=session_id,
        )
        if settings.use_mock_model_fallbacks:
            logger.info("chat_service using mock fallback after upstream connection error", session_id=session_id)
            return _build_mock_chat_response(message, style), None, "fallback-chat"
        raise UpstreamServiceUnavailable() from exc

    parsed = parse_with_retry(raw_output, chat_parser)
    return parsed, tool_used, settings.text_model


def handle_chat(user_id: str, session_id: str, message: str, style_override: str | None) -> dict:
    profile = get_user_profile(user_id)
    style = style_override or profile.get("preferred_style")
    message = sanitize_input(message)
    intent = classify_intent(message)

    logger.info("chat_service handling request", intent=intent, style=style, session_id=session_id)

    if intent == "weather":
        location = _resolve_weather_location(message, profile)
        weather_raw = get_weather.invoke({"location": location})
        parsed = parse_with_retry(weather_raw, weather_parser)
        add_turn(session_id, user_id, message, parsed)

        return build_response(
            session_id=session_id,
            parsed=parsed,
            model_used="weather-tool",
            tool_used="get_weather",
            style_applied=style,
        )

    parsed, tool_used, model_used = _run_text_agent(message, session_id, profile, style)
    add_turn(session_id, user_id, message, parsed)

    return build_response(
        session_id=session_id,
        parsed=parsed,
        model_used=model_used,
        tool_used=tool_used,
        style_applied=style,
    )
