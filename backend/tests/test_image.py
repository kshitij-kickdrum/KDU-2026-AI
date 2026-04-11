import io
from unittest.mock import MagicMock, patch

from openai import APIConnectionError, RateLimitError


class DummyRateLimitError(RateLimitError):
    def __init__(self):
        pass


class DummyAPIConnectionError(APIConnectionError):
    def __init__(self):
        pass


def test_unsupported_image_format_returns_400(client):
    fake_gif = io.BytesIO(b"GIF89a fake gif content")
    response = client.post(
        "/api/v1/image",
        data={"user_id": "u_001", "session_id": "sess_1"},
        files={"image": ("test.gif", fake_gif, "image/gif")},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "UNSUPPORTED_FORMAT"


def test_image_too_large_returns_400(client):
    large_image = io.BytesIO(b"x" * (11 * 1024 * 1024))
    response = client.post(
        "/api/v1/image",
        data={"user_id": "u_001", "session_id": "sess_1"},
        files={"image": ("big.jpg", large_image, "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "IMAGE_TOO_LARGE"


def test_valid_image_returns_correct_envelope(client):
    mock_result = {
        "session_id": "sess_1",
        "response": {
            "description": "A golden retriever on a park bench",
            "objects_detected": ["dog", "bench"],
            "scene_type": "outdoor",
            "confidence": "high",
        },
        "model_used": "gpt-4o-vision",
        "tool_used": None,
        "style_applied": None,
    }
    fake_image = io.BytesIO(b"fake jpeg bytes")
    with patch("app.api.routes.image.handle_image", return_value=mock_result):
        response = client.post(
            "/api/v1/image",
            data={"user_id": "u_001", "session_id": "sess_1"},
            files={"image": ("photo.jpg", fake_image, "image/jpeg")},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["model_used"] == "gpt-4o-vision"
    assert body["tool_used"] is None
    assert "description" in body["response"]


def test_image_uses_mock_fallback_when_upstream_rate_limited():
    from app.services.image_service import handle_image

    with patch("app.services.image_service._vision_llm") as mock_llm:
        mock_llm.invoke.side_effect = DummyRateLimitError()
        response = handle_image(
            session_id="sess_img_fallback",
            user_id="u_001",
            image_bytes=b"fakejpeg",
            content_type="image/jpeg",
            style="expert",
            prompt="What is in this image?",
        )

    assert response["model_used"] == "fallback-vision"
    assert response["tool_used"] is None
    assert "Development fallback" in response["response"]["description"]


def test_image_uses_mock_fallback_when_upstream_unavailable():
    from app.services.image_service import handle_image

    with patch("app.services.image_service._vision_llm") as mock_llm:
        mock_llm.invoke.side_effect = DummyAPIConnectionError()
        response = handle_image(
            session_id="sess_img_fallback_2",
            user_id="u_001",
            image_bytes=b"fakejpeg",
            content_type="image/jpeg",
            style="expert",
            prompt=None,
        )

    assert response["model_used"] == "fallback-vision"
    assert response["tool_used"] is None
    assert response["response"]["scene_type"] == "unknown"
