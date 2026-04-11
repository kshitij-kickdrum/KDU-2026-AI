from unittest.mock import patch
from openai import APIConnectionError, RateLimitError


class DummyRateLimitError(RateLimitError):
    def __init__(self):
        pass


class DummyAPIConnectionError(APIConnectionError):
    def __init__(self):
        pass


def test_unknown_user_returns_404(client):
    response = client.post("/api/v1/chat", json={
        "user_id": "u_999",
        "session_id": "sess_1",
        "message": "Hello",
    })
    assert response.status_code == 404
    assert response.json()["code"] == "USER_NOT_FOUND"


def test_blank_message_returns_422(client):
    response = client.post("/api/v1/chat", json={
        "user_id": "u_001",
        "session_id": "sess_1",
        "message": "   ",
    })
    assert response.status_code == 422


def test_invalid_style_returns_422(client):
    response = client.post("/api/v1/chat", json={
        "user_id": "u_001",
        "session_id": "sess_1",
        "message": "Hello",
        "style": "pirate",
    })
    assert response.status_code == 422


def test_chat_response_envelope_shape(client):
    mock_result = {
        "session_id": "sess_1",
        "response": {"answer": "The weather is sunny."},
        "model_used": "gpt-4o",
        "tool_used": None,
        "style_applied": "expert",
    }
    with patch("app.api.routes.chat.handle_chat", return_value=mock_result):
        response = client.post("/api/v1/chat", json={
            "user_id": "u_001",
            "session_id": "sess_1",
            "message": "What is the weather?",
        })
    assert response.status_code == 200
    body = response.json()
    assert "session_id" in body
    assert "response" in body
    assert "model_used" in body
    assert "tool_used" in body
    assert "style_applied" in body


def test_weather_keyword_routes_to_weather_intent():
    from app.agent.router import _keyword_match
    assert _keyword_match("what is the temperature today?") == "weather"
    assert _keyword_match("will it rain tomorrow?") == "weather"
    assert _keyword_match("tell me a joke") is None


def test_image_intent_detected_with_flag():
    from app.agent.router import classify_intent
    assert classify_intent("describe this", has_image=True) == "image"


def test_classifier_fallback_routes_non_keyword_messages():
    from app.agent.router import classify_intent

    with patch("app.agent.router._classifier_llm") as mock_llm:
        mock_llm.invoke.return_value.content = "chat"
        assert classify_intent("tell me a joke") == "chat"


def test_classifier_fallback_can_route_weather():
    from app.agent.router import classify_intent

    with patch("app.agent.router._classifier_llm") as mock_llm:
        mock_llm.invoke.return_value.content = "weather"
        assert classify_intent("is it nice outside where i live") == "weather"


def test_chat_uses_mock_fallback_when_upstream_rate_limited():
    from app.services.chat_service import handle_chat

    with patch("app.services.chat_service.run_agent", side_effect=DummyRateLimitError()):
        response = handle_chat("u_001", "sess_fallback_chat", "What is a cow?", "expert")

    assert response["model_used"] == "fallback-chat"
    assert response["tool_used"] is None
    assert "upstream AI provider is currently unavailable" in response["response"]["answer"]


def test_chat_uses_mock_fallback_when_upstream_unavailable():
    from app.services.chat_service import handle_chat

    with patch("app.services.chat_service.run_agent", side_effect=DummyAPIConnectionError()):
        response = handle_chat("u_001", "sess_fallback_chat_2", "Explain planets", "child")

    assert response["model_used"] == "fallback-chat"
    assert response["tool_used"] is None
    assert "backup reply" in response["response"]["answer"]
