"""FlowState visualization helpers."""

from __future__ import annotations

from typing import Any

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None  # type: ignore[assignment]


def get_flow_state_rows(state: dict[str, Any]) -> list[dict[str, str]]:
    """Return FlowState key/value rows suitable for dataframe display."""
    keys = (
        "fact_check_status",
        "iteration_counter",
        "execution_start_time",
        "last_updated",
    )
    return [{"field": key, "value": str(state.get(key, ""))} for key in keys]


def render_flow_state(result: dict[str, Any]) -> None:
    """Render the FlowState visualizer for flow executions."""
    if st is None:
        return
    state = result.get("state")
    if not isinstance(state, dict):
        return
    st.subheader("FlowState")
    cols = st.columns(2)
    cols[0].metric("Fact-check status", str(state.get("fact_check_status", "")))
    cols[1].metric("Iteration", str(state.get("iteration_counter", "")))
    st.dataframe(get_flow_state_rows(state), hide_index=True, use_container_width=True)
