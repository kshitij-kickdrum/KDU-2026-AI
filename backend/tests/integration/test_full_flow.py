from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_chat_stream_and_usage_stats_flow():
    session_id = "sess_integration_1"
    with client.stream(
        "POST",
        "/chat/stream",
        json={"message": "calculate 4+4", "session_id": session_id, "stream": True},
    ) as response:
        assert response.status_code == 200
        chunks = list(response.iter_text())
        assert any("data:" in chunk for chunk in chunks)

    stats = client.get("/usage/stats", params={"session_id": session_id})
    assert stats.status_code == 200
    payload = stats.json()
    assert payload["requests_count"] == 1
    assert payload["total_tokens"] >= 0
