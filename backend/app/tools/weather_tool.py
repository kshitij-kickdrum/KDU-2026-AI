import json
from pathlib import Path

from langchain_core.tools import tool

from app.core.config import settings
from app.core.exceptions import ToolCallFailed
from app.core.logging import get_logger

logger = get_logger(__name__)

_MOCK_PATH = Path(__file__).parent.parent.parent / "data" / "mock_weather.json"

with _MOCK_PATH.open(encoding="utf-8") as f:
    _mock_data: dict = json.load(f)


def _normalize_location(location: str) -> str:
    return " ".join(location.strip().lower().split())


def _get_mock_weather(location: str) -> dict:
    normalized = _normalize_location(location)

    for key, value in _mock_data.items():
        if key == "default":
            continue
        if _normalize_location(key) == normalized:
            return dict(value)

    data = dict(_mock_data["default"])
    if location.strip():
        data["location"] = location.strip()
    return data


def _get_live_weather(location: str) -> dict:
    import httpx

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": location, "appid": settings.weather_api_key, "units": "metric"}

    response = httpx.get(url, params=params, timeout=5, trust_env=False)
    response.raise_for_status()
    data = response.json()

    return {
        "temperature": f"{data['main']['temp']}°C",
        "feels_like": f"{data['main']['feels_like']}°C",
        "summary": data["weather"][0]["description"].capitalize(),
        "location": location,
        "advice": "",
    }


@tool
def get_weather(location: str) -> str:
    """
    Fetches current weather data for the given location.
    Returns temperature, feels_like, summary, location, and advice as a JSON string.
    """
    logger.info("weather_tool called", location=location)

    if settings.use_mock_weather:
        data = _get_mock_weather(location)
        data["data_source"] = "mock"
        logger.info("weather_tool using mock data", location=location)
        return json.dumps(data)

    try:
        data = _get_live_weather(location)
        data["data_source"] = "live"
        logger.info("weather_tool using live data", location=location)
        return json.dumps(data)
    except Exception as exc:
        logger.warning(
            "weather_tool live call failed",
            location=location,
            error=str(exc),
        )
        raise ToolCallFailed() from exc
