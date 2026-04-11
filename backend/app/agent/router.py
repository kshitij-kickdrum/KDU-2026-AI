from openai import APIConnectionError, APIStatusError, RateLimitError

from app.core.config import settings
from app.core.llm import build_chat_model
from app.core.logging import get_logger

logger = get_logger(__name__)

_WEATHER_KEYWORDS = {"weather", "temperature", "forecast", "humid", "rain", "sunny", "cold", "hot", "climate"}
_classifier_llm = build_chat_model(
    model=settings.classifier_model,
    api_key=settings.classifier_model_api_key,
)

_CLASSIFIER_PROMPT = (
    "Classify the user's request into one of exactly two labels: weather or chat.\n"
    "Return only one word: weather or chat.\n\n"
    "User message: {message}"
)


def _keyword_match(message: str) -> str | None:
    lowered = message.lower()
    if any(kw in lowered for kw in _WEATHER_KEYWORDS):
        return "weather"
    return None


def _classify_with_llm(message: str) -> str:
    try:
        response = _classifier_llm.invoke(_CLASSIFIER_PROMPT.format(message=message))
    except (RateLimitError, APIStatusError, APIConnectionError) as exc:
        logger.warning(
            "router: classifier fallback failed, defaulting to chat",
            error_type=type(exc).__name__,
        )
        return "chat"

    content = str(response.content).strip().lower()
    if "weather" in content:
        return "weather"
    return "chat"


def classify_intent(message: str, has_image: bool = False) -> str:
    if has_image:
        logger.info("router: image detected, routing to vision pipeline")
        return "image"

    matched = _keyword_match(message)
    if matched:
        logger.info("router: keyword match", intent=matched, message=message)
        return matched

    inferred = _classify_with_llm(message)
    logger.info("router: classifier fallback", intent=inferred, message=message)
    return inferred
