"""Reusable Streamlit components."""

from __future__ import annotations

import os
from typing import Any

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None  # type: ignore[assignment]


MODE_OPTIONS = ("sequential", "hierarchical", "flow")


def render_topic_input() -> tuple[str, str, bool]:
    """Render topic input, mode selector, and run button."""
    if st is None:
        return "", "sequential", False
    topic = st.text_input("Research topic", placeholder="AI in healthcare")
    mode = st.radio("Execution mode", MODE_OPTIONS, horizontal=True)
    run_clicked = st.button("Run research", type="primary")
    return topic, mode, run_clicked


def render_environment_status() -> None:
    """Render environment variable readiness indicators in the sidebar."""
    if st is None:
        return
    st.sidebar.subheader("Environment")
    llm_ready = bool(os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY"))
    serper_ready = bool(os.getenv("SERPER_API_KEY"))
    st.sidebar.write(f"[{'OK' if llm_ready else 'MISSING'}] LLM provider")
    st.sidebar.write(f"[{'OK' if serper_ready else 'MISSING'}] SERPER_API_KEY")


def extract_agent_outputs(result: dict[str, Any]) -> dict[str, str]:
    """Return display-ready agent outputs from workflow result data."""
    if "agent_outputs" in result and isinstance(result["agent_outputs"], dict):
        outputs = result["agent_outputs"]
        return {
            "researcher": str(outputs.get("researcher", "")),
            "fact_checker": str(outputs.get("fact_checker", "")),
            "writer": str(outputs.get("writer", result.get("final_output", ""))),
        }
    state = result.get("state", {})
    if isinstance(state, dict):
        return {
            "researcher": str(state.get("research_results") or ""),
            "fact_checker": str(state.get("fact_check_details") or ""),
            "writer": str(result.get("final_output", "")),
        }
    return {
        "researcher": "",
        "fact_checker": "",
        "writer": str(result.get("final_output", "")),
    }


def render_agent_output_section(result: dict[str, Any]) -> None:
    """Render stage-based output expanders for each agent."""
    if st is None:
        return
    labels = {
        "researcher": "Researcher",
        "fact_checker": "Fact-Checker",
        "writer": "Writer",
    }
    for key, output in extract_agent_outputs(result).items():
        with st.expander(labels[key], expanded=bool(output)):
            st.markdown(output or "_No output captured for this stage._")
