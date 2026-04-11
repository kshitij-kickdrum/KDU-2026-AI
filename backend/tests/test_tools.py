import json
from unittest.mock import patch

import pytest

from app.core.exceptions import ToolCallFailed
from app.tools.weather_tool import _get_mock_weather, get_weather


def test_mock_weather_known_city():
    data = _get_mock_weather("Mumbai, India")
    assert data["location"] == "Mumbai, India"
    assert "temperature" in data


def test_mock_weather_unknown_city_preserves_requested_location():
    data = _get_mock_weather("Atlantis")
    assert data["location"] == "Atlantis"
    assert "temperature" in data


def test_weather_tool_uses_mock_when_env_set():
    with patch("app.tools.weather_tool.settings") as mock_settings:
        mock_settings.use_mock_weather = True
        result = get_weather.invoke({"location": "Mumbai, India"})

    assert "temperature" in result
    assert "mock" in result


def test_weather_tool_raises_when_live_call_fails():
    with patch("app.tools.weather_tool.settings") as mock_settings:
        mock_settings.use_mock_weather = False
        mock_settings.weather_api_key = "bad_key"
        with patch("app.tools.weather_tool._get_live_weather", side_effect=Exception("API down")):
            with pytest.raises(ToolCallFailed):
                get_weather.invoke({"location": "Delhi, India"})


def test_weather_tool_returns_json_string():
    with patch("app.tools.weather_tool.settings") as mock_settings:
        mock_settings.use_mock_weather = True
        result = get_weather.invoke({"location": "London, UK"})

    parsed = json.loads(result)
    assert isinstance(parsed, dict)
    assert "temperature" in parsed
