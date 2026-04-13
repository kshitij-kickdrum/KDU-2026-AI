from fastapi.testclient import TestClient

from app.main import app


def test_evaluate_route_returns_enriched_summary(monkeypatch):
    from app.evaluation import evaluator

    def fake_run_evaluation():
        return {
            "results": [
                {
                    "name": "basic_case",
                    "thread_id": "thread-123",
                    "interrupted": True,
                    "approved": False,
                    "metrics": [
                        {"key": "portfolio_computed", "score": 1, "comment": "ok"},
                        {"key": "trade_log_on_approval", "score": 1, "comment": "ok"},
                    ],
                }
            ],
            "token_summary": {
                "tracked": True,
                "observed_runs": 1,
                "total_tokens": 120,
                "prompt_tokens": 60,
                "completion_tokens": 60,
                "total_cost": 0.001,
                "note": None,
            },
            "logging_summary": {
                "logged": True,
                "feedback_count": 2,
                "fallback_runs_logged": 0,
                "note": None,
            },
        }

    monkeypatch.setattr(evaluator, "run_evaluation", fake_run_evaluation)

    client = TestClient(app)
    response = client.post("/api/v1/evaluate")

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "completed"
    assert payload["total_metrics"] == 2
    assert payload["passed_metrics"] == 2
    assert payload["pass_rate"] == 100.0

    assert "token_summary" in payload
    assert payload["token_summary"]["total_tokens"] == 120

    assert "logging_summary" in payload
    assert payload["logging_summary"]["feedback_count"] == 2

    assert len(payload["results"]) == 1
    result = payload["results"][0]
    assert result["thread_id"] == "thread-123"
    assert len(result["metrics"]) == 2
