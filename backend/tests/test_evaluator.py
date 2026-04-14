import pytest

from app.evaluation import evaluator


class _Snapshot:
    def __init__(self, values):
        self.values = values


class _FakeGraph:
    def __init__(self):
        self.approved = False

    def invoke(self, state, config):
        if state is None and self.approved:
            return {
                "portfolio_total_usd": 1000.0,
                "pending_action": "buy",
                "error": None,
                "portfolio_total_converted": None,
                "exchange_rate": None,
                "trade_log": ["2026-04-14T00:00:00 - BUY 10 shares of AAPL at $352.42"],
            }
        raise RuntimeError("interrupt: awaiting approval")

    def get_state(self, config):
        return _Snapshot(
            {
                "portfolio_total_usd": 1000.0,
                "pending_action": "buy",
                "error": None,
                "portfolio_total_converted": None,
                "exchange_rate": None,
                "trade_log": [],
            }
        )

    def update_state(self, config, update):
        self.approved = bool(update.get("action_approved"))


class _FakeGraphNoException:
    def __init__(self):
        self.approved = False

    def invoke(self, state, config):
        if state is None and self.approved:
            return {
                "portfolio_total_usd": 1000.0,
                "pending_action": "buy",
                "action_approved": True,
                "error": None,
                "portfolio_total_converted": None,
                "exchange_rate": None,
                "trade_log": ["2026-04-14T00:00:00 - BUY 10 shares of AAPL at $352.42"],
            }
        return {
            "portfolio_total_usd": 1000.0,
            "pending_action": "buy",
            "action_approved": False,
            "error": None,
            "portfolio_total_converted": None,
            "exchange_rate": None,
            "trade_log": [],
        }

    def get_state(self, config):
        return _Snapshot(self.invoke({}, config))

    def update_state(self, config, update):
        self.approved = bool(update.get("action_approved"))


class _Run:
    def __init__(self, run_id, thread_id, tokens, cost):
        self.id = run_id
        self.extra = {"metadata": {"thread_id": thread_id}}
        self.usage_metadata = {
            "input_tokens": tokens // 2,
            "output_tokens": tokens // 2,
            "total_tokens": tokens,
        }
        self.total_tokens = tokens
        self.total_cost = cost


class _FakeClient:
    def __init__(self, runs=None):
        self._runs = runs or []
        self.feedback_calls = []
        self.run_calls = []

    def list_runs(self, **kwargs):
        return self._runs

    def create_feedback(self, **kwargs):
        self.feedback_calls.append(kwargs)

    def create_run(self, **kwargs):
        self.run_calls.append(kwargs)


def test_run_test_case_includes_approval_metric_and_resumes_on_approval(monkeypatch):
    monkeypatch.setattr(evaluator, "graph", _FakeGraph())

    test_case = {
        "name": "approved_case",
        "input": {
            "portfolio": [],
            "currency": "USD",
            "symbol": "AAPL",
            "approve": True,
        },
    }

    result = evaluator.run_test_case(test_case)

    metric_keys = [m["key"] for m in result["metrics"]]
    assert "trade_log_on_approval" in metric_keys

    approval_metric = next(m for m in result["metrics"] if m["key"] == "trade_log_on_approval")
    assert approval_metric["score"] == 1
    assert result["approved"] is True


def test_summarize_token_usage_aggregates_runs(monkeypatch):
    fake_client = _FakeClient(
        runs=[
            _Run("run-1", "thread-a", 120, 0.002),
            _Run("run-2", "thread-b", 80, 0.001),
            _Run("run-3", "thread-x", 999, 1.0),
        ]
    )
    monkeypatch.setattr(evaluator, "client", fake_client)

    summary = evaluator.summarize_token_usage(["thread-a", "thread-b"])

    assert summary["tracked"] is True
    assert summary["observed_runs"] == 2
    assert summary["total_tokens"] == 200
    assert summary["total_cost"] == pytest.approx(0.003)


def test_run_test_case_resumes_when_pending_without_interrupt(monkeypatch):
    monkeypatch.setattr(evaluator, "graph", _FakeGraphNoException())

    test_case = {
        "name": "approved_case_no_interrupt",
        "input": {
            "portfolio": [],
            "currency": "USD",
            "symbol": "AAPL",
            "approve": True,
        },
    }

    result = evaluator.run_test_case(test_case)
    approval_metric = next(m for m in result["metrics"] if m["key"] == "trade_log_on_approval")

    assert result["interrupted"] is True
    assert approval_metric["score"] == 1


def test_log_evaluation_results_writes_feedback(monkeypatch):
    fake_client = _FakeClient(runs=[_Run("run-1", "thread-a", 100, 0.001)])
    monkeypatch.setattr(evaluator, "client", fake_client)

    results = [
        {
            "name": "case",
            "thread_id": "thread-a",
            "approved": False,
            "metrics": [
                {"key": "portfolio_computed", "score": 1, "comment": "ok"},
                {"key": "trade_log_on_approval", "score": 1, "comment": "ok"},
            ],
        }
    ]

    logging_summary = evaluator.log_evaluation_results(results)

    assert logging_summary["logged"] is True
    assert logging_summary["feedback_count"] == 2
    assert len(fake_client.feedback_calls) == 2
