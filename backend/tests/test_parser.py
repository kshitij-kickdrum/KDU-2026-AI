import pytest
from langchain_core.exceptions import OutputParserException
from unittest.mock import MagicMock, patch

from app.parsers.weather_parser import parser as weather_parser
from app.parsers.chat_parser import parser as chat_parser
from app.parsers.image_parser import parser as image_parser
from app.parsers.retry import parse_with_retry
from app.core.exceptions import ParseError


def test_weather_parser_valid():
    raw = '{"temperature": "32C", "feels_like": "36C", "summary": "Hot", "location": "Mumbai", "advice": "Stay hydrated"}'
    result = parse_with_retry(raw, weather_parser)
    assert result["temperature"] == "32C"
    assert result["location"] == "Mumbai"


def test_chat_parser_valid():
    raw = '{"answer": "The sky is blue."}'
    result = parse_with_retry(raw, chat_parser)
    assert result["answer"] == "The sky is blue."
    assert result["follow_up"] is None


def test_image_parser_valid():
    raw = '{"description": "A dog", "objects_detected": ["dog", "bench"], "scene_type": "outdoor", "confidence": "high"}'
    result = parse_with_retry(raw, image_parser)
    assert result["description"] == "A dog"
    assert "dog" in result["objects_detected"]


def test_parse_raises_parse_error_after_max_retries():
    bad_raw = "this is not json at all {{{"
    mock_response = MagicMock()
    mock_response.content = "still not json"

    with patch("app.parsers.retry._fix_llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        with pytest.raises(ParseError) as exc_info:
            parse_with_retry(bad_raw, weather_parser)

    assert exc_info.value.code == "PARSE_ERROR"
    assert exc_info.value.status_code == 422


def test_parse_succeeds_on_retry():
    bad_raw = "not json"
    fixed_raw = '{"temperature": "20C", "feels_like": "18C", "summary": "Cool", "location": "London", "advice": "Wear a jacket"}'
    mock_response = MagicMock()
    mock_response.content = fixed_raw

    with patch("app.parsers.retry._fix_llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        result = parse_with_retry(bad_raw, weather_parser)

    assert result["location"] == "London"
