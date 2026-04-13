"""
LangSmith Evaluator for the Stock Trading Agent

Exercise 2 requirement: Evaluate the agent using basic evaluation metrics.

This script:
1. Runs the agent against a set of test cases
2. Scores each run against defined metrics
3. Logs results to LangSmith as an evaluation dataset
4. Prints a summary of token usage and costs

Run with:
    python -m app.evaluation.evaluator
"""

import os
import uuid
from langsmith import Client

from app.agent.graph import graph
from app.agent.state import Holding
from app.config import settings

# Set LangSmith env vars explicitly so they're active for this script
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

# LangSmith client
client = Client()


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

TEST_CASES = [
    {
        "name": "basic_usd_run",
        "input": {
            "portfolio": [
                Holding(symbol="AAPL", quantity=10, avg_buy_price=150.0),
                Holding(symbol="TSLA", quantity=5, avg_buy_price=200.0),
            ],
            "currency": "USD",
            "symbol": "AAPL",
            "approve": True,
        },
        "expected_fields": ["portfolio_total_usd", "pending_action"],
    },
    {
        "name": "inr_conversion_run",
        "input": {
            "portfolio": [
                Holding(symbol="NVDA", quantity=8, avg_buy_price=480.0),
            ],
            "currency": "INR",
            "symbol": "NVDA",
            "approve": False,
        },
        "expected_fields": ["portfolio_total_usd", "portfolio_total_converted", "exchange_rate"],
    },
    {
        "name": "eur_conversion_run",
        "input": {
            "portfolio": [
                Holding(symbol="MSFT", quantity=20, avg_buy_price=310.0),
            ],
            "currency": "EUR",
            "symbol": "MSFT",
            "approve": False,
        },
        "expected_fields": ["portfolio_total_usd", "portfolio_total_converted", "exchange_rate"],
    },
    {
        "name": "empty_portfolio_run",
        "input": {
            "portfolio": [],
            "currency": "USD",
            "symbol": "AAPL",
            "approve": False,
        },
        "expected_fields": ["portfolio_total_usd"],
    },
]


# ---------------------------------------------------------------------------
# Metric functions
# ---------------------------------------------------------------------------

def metric_portfolio_computed(run_output: dict) -> dict:
    """Check that portfolio_total_usd was computed and is a non-negative number."""
    total = run_output.get("portfolio_total_usd")
    passed = isinstance(total, (int, float)) and total >= 0
    return {
        "key": "portfolio_computed",
        "score": 1 if passed else 0,
        "comment": f"portfolio_total_usd = {total}"
    }


def metric_pending_action_valid(run_output: dict) -> dict:
    """Check that pending_action is one of the valid values (BUY/SELL only)."""
    action = run_output.get("pending_action")
    passed = action in ["buy", "sell"]
    return {
        "key": "pending_action_valid",
        "score": 1 if passed else 0,
        "comment": f"pending_action = {action}"
    }


def metric_no_crash(run_output: dict) -> dict:
    """Check that the run completed without an unhandled error."""
    error = run_output.get("error")
    passed = error is None
    return {
        "key": "no_crash",
        "score": 1 if passed else 0,
        "comment": f"error = {error}"
    }


def metric_currency_conversion(run_output: dict, currency: str) -> dict:
    """Check that currency conversion ran when currency is not USD."""
    if currency == "USD":
        passed = run_output.get("portfolio_total_converted") is None
        comment = "USD: no conversion expected"
    else:
        converted = run_output.get("portfolio_total_converted")
        rate = run_output.get("exchange_rate")
        passed = isinstance(converted, float) and isinstance(rate, float) and converted > 0
        comment = f"{currency}: converted={converted}, rate={rate}"
    return {
        "key": "currency_conversion_correct",
        "score": 1 if passed else 0,
        "comment": comment
    }


def metric_trade_log_on_approval(run_output: dict, approved: bool) -> dict:
    """Check that trade_log grows when a trade is approved."""
    trade_log = run_output.get("trade_log", [])
    if approved:
        passed = len(trade_log) > 0
        comment = f"Trade log has {len(trade_log)} entries after approval"
    else:
        passed = True  # Not applicable if no approval happened
        comment = "No approval in this run"
    return {
        "key": "trade_log_on_approval",
        "score": 1 if passed else 0,
        "comment": comment
    }


# ---------------------------------------------------------------------------
# Run a single test case and collect metrics
# ---------------------------------------------------------------------------

def run_test_case(test_case: dict) -> dict:
    """Run one test case and return metrics + output."""
    thread_id = f"eval-{test_case['name']}-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "messages": [],
        "user_prompt": "Evaluation run",
        "portfolio": test_case["input"]["portfolio"],
        "portfolio_total_usd": 0.0,
        "currency": test_case["input"]["currency"],
        "portfolio_total_converted": None,
        "exchange_rate": None,
        "pending_action": "buy",
        "action_approved": False,
        "trade_log": [],
        "error": None,
        "symbol": test_case["input"]["symbol"],
    }

    final_state = {}
    interrupted = False
    approved = bool(test_case["input"].get("approve", False))

    def _is_pending_approval(state: dict) -> bool:
        action = state.get("pending_action")
        action_approved = bool(state.get("action_approved"))
        return action in {"buy", "sell"} and not action_approved

    try:
        final_state = graph.invoke(initial_state, config)
    except Exception as e:
        if "interrupt" in str(e).lower():
            # HITL interrupt — read state from checkpoint
            interrupted = True
            snapshot = graph.get_state(config)
            final_state = snapshot.values if snapshot else {}

            if approved:
                graph.update_state(config, {"action_approved": True})
                final_state = graph.invoke(None, config)
        else:
            final_state = {"error": str(e), "portfolio_total_usd": 0.0,
                           "pending_action": "buy", "trade_log": []}

    # Newer graph runtimes may return checkpointed pending state without raising.
    if _is_pending_approval(final_state):
        interrupted = True
        if approved:
            graph.update_state(config, {"action_approved": True})
            final_state = graph.invoke(None, config)

    # Collect metrics
    metrics = [
        metric_portfolio_computed(final_state),
        metric_pending_action_valid(final_state),
        metric_no_crash(final_state),
        metric_currency_conversion(final_state, test_case["input"]["currency"]),
        metric_trade_log_on_approval(final_state, approved),
    ]

    return {
        "name": test_case["name"],
        "thread_id": thread_id,
        "interrupted": interrupted,
        "approved": approved,
        "final_state": final_state,
        "metrics": metrics,
    }


def _extract_thread_id(run) -> str | None:
    """Extract thread_id from LangSmith run metadata when available."""
    extra = getattr(run, "extra", None) or {}
    metadata = extra.get("metadata", {}) if isinstance(extra, dict) else {}
    thread_id = metadata.get("thread_id") if isinstance(metadata, dict) else None
    return str(thread_id) if thread_id else None


def _accumulate_run_usage(summary: dict, run) -> None:
    """Merge token and cost usage from one LangSmith run into summary."""
    usage = getattr(run, "usage_metadata", None) or {}
    has_usage_dict = isinstance(usage, dict)

    if has_usage_dict:
        summary["prompt_tokens"] += int(usage.get("input_tokens", 0) or 0)
        summary["completion_tokens"] += int(usage.get("output_tokens", 0) or 0)
        summary["total_tokens"] += int(usage.get("total_tokens", 0) or 0)

    if not has_usage_dict or int(usage.get("total_tokens", 0) or 0) == 0:
        summary["total_tokens"] += int(getattr(run, "total_tokens", 0) or 0)

    total_cost = getattr(run, "total_cost", None)
    if isinstance(total_cost, (int, float)):
        summary["total_cost"] += float(total_cost)


def summarize_token_usage(thread_ids: list[str]) -> dict:
    """Compute token/cost totals for the evaluated threads from LangSmith."""
    summary = {
        "tracked": False,
        "observed_runs": 0,
        "total_tokens": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_cost": 0.0,
        "note": None,
    }

    try:
        runs = list(client.list_runs(project_name=settings.langchain_project, limit=100))
        target_threads = set(thread_ids)

        for run in runs:
            run_thread_id = _extract_thread_id(run)
            if run_thread_id not in target_threads:
                continue

            summary["observed_runs"] += 1
            _accumulate_run_usage(summary, run)

        summary["tracked"] = summary["observed_runs"] > 0
        if not summary["tracked"]:
            summary["note"] = "No LangSmith runs found for current evaluation threads."
        elif summary["total_tokens"] == 0:
            summary["note"] = "Tracing active, but token/cost details were not available for these runs."

    except Exception as exc:
        summary["note"] = f"LangSmith summary unavailable: {exc}"

    return summary


def log_evaluation_results(results: list[dict]) -> dict:
    """Log evaluation outcomes to LangSmith so results are persisted beyond console output."""
    logging_summary = {
        "logged": False,
        "feedback_count": 0,
        "fallback_runs_logged": 0,
        "note": None,
    }

    try:
        runs = list(client.list_runs(project_name=settings.langchain_project, limit=100))
        run_by_thread = {}
        for run in runs:
            thread_id = _extract_thread_id(run)
            if thread_id and thread_id not in run_by_thread:
                run_by_thread[thread_id] = run

        for result in results:
            thread_id = result["thread_id"]
            target_run = run_by_thread.get(thread_id)

            if target_run is not None:
                for metric in result["metrics"]:
                    client.create_feedback(
                        run_id=target_run.id,
                        key=metric["key"],
                        score=float(metric["score"]),
                        comment=metric["comment"],
                    )
                    logging_summary["feedback_count"] += 1
                continue

            # Fallback: still persist an explicit evaluation record when a trace run is unavailable.
            client.create_run(
                name=f"evaluation::{result['name']}",
                run_type="chain",
                project_name=settings.langchain_project,
                inputs={"thread_id": thread_id, "approved": result["approved"]},
                outputs={"metrics": result["metrics"]},
            )
            logging_summary["fallback_runs_logged"] += 1

        logging_summary["logged"] = (
            logging_summary["feedback_count"] > 0
            or logging_summary["fallback_runs_logged"] > 0
        )
        if not logging_summary["logged"]:
            logging_summary["note"] = "No evaluation artifacts were logged to LangSmith."

    except Exception as exc:
        logging_summary["note"] = f"LangSmith logging unavailable: {exc}"

    return logging_summary


# ---------------------------------------------------------------------------
# Main evaluation runner
# ---------------------------------------------------------------------------

def run_evaluation():
    """Run all test cases and print a summary report."""
    print("\n" + "=" * 60)
    print("  STOCK TRADING AGENT — EVALUATION REPORT")
    print("=" * 60)
    print(f"  LangSmith Project : {settings.langchain_project}")
    print(f"  Model             : {settings.openai_model}")
    print("=" * 60 + "\n")

    all_results = []

    for test_case in TEST_CASES:
        print(f"▶ Running: {test_case['name']} ...")
        result = run_test_case(test_case)
        all_results.append(result)

        # Print per-test summary
        print(f"  Thread ID  : {result['thread_id']}")
        print(f"  Interrupted: {result['interrupted']} (HITL triggered)")
        print("  Metrics:")
        for m in result["metrics"]:
            status = "✅" if m["score"] == 1 else "❌"
            print(f"    {status} {m['key']}: {m['comment']}")
        print()

    # Overall score
    total_metrics = sum(len(r["metrics"]) for r in all_results)
    passed_metrics = sum(
        sum(1 for m in r["metrics"] if m["score"] == 1)
        for r in all_results
    )

    thread_ids = [result["thread_id"] for result in all_results]
    token_summary = summarize_token_usage(thread_ids)
    logging_summary = log_evaluation_results(all_results)

    print("=" * 60)
    print(f"  OVERALL SCORE: {passed_metrics}/{total_metrics} metrics passed")
    print(f"  PASS RATE    : {passed_metrics / total_metrics * 100:.1f}%")
    print("=" * 60)
    print()
    print("  Token usage and cost summary:")
    print(f"  → Project        : '{settings.langchain_project}'")
    print(f"  → Observed runs  : {token_summary['observed_runs']}")
    print(f"  → Total tokens   : {token_summary['total_tokens']}")
    print(f"  → Prompt tokens  : {token_summary['prompt_tokens']}")
    print(f"  → Completion toks: {token_summary['completion_tokens']}")
    print(f"  → Total cost     : ${token_summary['total_cost']:.6f}")
    if token_summary["note"]:
        print(f"  → Note           : {token_summary['note']}")
    print()
    print("  LangSmith evaluation logging:")
    print(f"  → Feedback logged : {logging_summary['feedback_count']}")
    print(f"  → Fallback runs   : {logging_summary['fallback_runs_logged']}")
    if logging_summary["note"]:
        print(f"  → Note            : {logging_summary['note']}")
    print()
    print("  Evaluation complete.")
    print("=" * 60 + "\n")

    return {
        "results": all_results,
        "token_summary": token_summary,
        "logging_summary": logging_summary,
    }


if __name__ == "__main__":
    run_evaluation()
