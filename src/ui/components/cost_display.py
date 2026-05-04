from __future__ import annotations

import streamlit as st

from src.models.file_models import CostSummary


def render_cost_display(summary: CostSummary) -> None:
    st.metric("Total Cost (USD)", f"${summary.total_cost_usd:.6f}")
    st.metric("Total Tokens", f"{summary.total_tokens}")
    st.write("Breakdown by operation")
    st.json(summary.by_operation)
