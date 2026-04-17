from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import create_app


class StubResponse:
    def __init__(self, text: str) -> None:
        self.text = text
        self.prompt_tokens = 10
        self.completion_tokens = 20


def test_health_endpoint() -> None:
    app = create_app()
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        payload = r.json()
        assert "status" in payload


def test_query_endpoint() -> None:
    app = create_app()
    with TestClient(app) as client:
        services = client.app.state.services

        async def fake_complete(model_key: str, prompt: str, query: str):
            return StubResponse("mocked")

        services.llm_client.complete = fake_complete
        r = client.post(
            "/query",
            json={
                "query": f"How can I reset my account password? {uuid4()}",
                "override_category": "faq",
                "override_complexity": "low",
            },
        )
        assert r.status_code == 200
        payload = r.json()
        assert payload["response"] == "mocked"
        assert payload["cache_hit"] is False


def test_admin_reload_endpoint() -> None:
    app = create_app()
    with TestClient(app) as client:
        r = client.post("/admin/config/reload")
        assert r.status_code == 200
        assert r.json()["message"] == "Configuration reloaded successfully"
