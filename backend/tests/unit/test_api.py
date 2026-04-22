from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert "status" in payload
    assert "services" in payload


def test_usage_not_found():
    response = client.get("/usage/stats", params={"session_id": "sess_missing"})
    assert response.status_code == 404

