"""Execution stats panel for Streamlit."""

from __future__ import annotations

from typing import Any

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None  # type: ignore[assignment]


def format_stats(result: dict[str, Any], mode: str) -> dict[str, str]:
    """Format workflow result values for display."""
    cost = result.get("cost", {})
    estimated = ""
    total_tokens = ""
    if isinstance(cost, dict):
        estimated = str(cost.get("estimated_usd", "0"))
        total_tokens = str(cost.get("total_tokens", "0"))
    return {
        "Mode": mode,
        "Status": str(result.get("status", "completed")),
        "Execution ID": str(result.get("execution_id", "")),
        "Duration": f"{float(result.get('duration_sec', 0.0)):.2f}s",
        "Iterations": str(result.get("iterations_used", 1)),
        "Estimated cost": f"${estimated}",
        "Total tokens": total_tokens,
    }


def render_stats_panel(result: dict[str, Any], mode: str) -> None:
    """Render execution stats as Streamlit metrics."""
    if st is None:
        return
    stats = format_stats(result, mode)
    st.subheader("Execution Stats")
    cols = st.columns(4)
    metric_items = [
        ("Mode", stats["Mode"]),
        ("Status", stats["Status"]),
        ("Duration", stats["Duration"]),
        ("Iterations", stats["Iterations"]),
    ]
    for column, (label, value) in zip(cols, metric_items):
        column.metric(label, value)
    st.caption(
        f"Execution ID: {stats['Execution ID']} | "
        f"Estimated cost: {stats['Estimated cost']} | "
        f"Total tokens: {stats['Total tokens']}"
    )
