"""Streamlit entry point for the CrewAI research system."""

from __future__ import annotations

from typing import Any

from dotenv import load_dotenv

from src.agents.factory import build_agents
from src.config.loader import (
    get_config_paths,
    get_llm_provider,
    load_agents_config,
    load_tasks_config,
)
from src.memory.manager import MemoryManager
from src.ui.components import (
    render_agent_output_section,
    render_environment_status,
    render_topic_input,
)
from src.ui.flow_state_view import render_flow_state
from src.ui.history_view import render_history
from src.ui.stats_panel import render_stats_panel
from src.utils.cost_tracker import CostTracker
from src.utils.logger import get_logger
from src.utils.validation import validate_topic
from src.workflows.flow import run_flow
from src.workflows.hierarchical import run_hierarchical
from src.workflows.sequential import run_sequential

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None  # type: ignore[assignment]


logger = get_logger(__name__)


def run_research_from_ui(topic: str, mode: str) -> dict[str, Any]:
    """Run the selected workflow from Streamlit input."""
    cleaned_topic = validate_topic(topic)
    llm = get_llm_provider()
    agents_path, tasks_path = get_config_paths()
    agents_config = load_agents_config(agents_path)
    tasks_config = load_tasks_config(tasks_path)
    memory_manager = MemoryManager()
    cost_tracker = CostTracker()
    agents = build_agents(agents_config, llm)
    try:
        if mode == "flow":
            return run_flow(
                cleaned_topic, agents, tasks_config, memory_manager, cost_tracker
            )
        if mode == "hierarchical":
            return run_hierarchical(
                cleaned_topic,
                agents,
                tasks_config,
                llm,
                memory_manager,
                cost_tracker,
            )
        return run_sequential(
            cleaned_topic, agents, tasks_config, memory_manager, cost_tracker
        )
    finally:
        memory_manager.close()


def render_app() -> None:
    """Render and run the Streamlit app."""
    if st is None:
        raise RuntimeError("streamlit is not installed")

    load_dotenv()
    st.set_page_config(page_title="CrewAI Research System", layout="wide")
    st.title("CrewAI Research System")
    st.caption("Run multi-agent research with YAML-configured agents and memory.")

    render_environment_status()
    show_history = st.sidebar.toggle("Show history", value=False)
    if show_history:
        history_manager = MemoryManager()
        try:
            render_history(history_manager)
        finally:
            history_manager.close()

    topic, mode, run_clicked = render_topic_input()
    if not run_clicked:
        return

    try:
        with st.spinner("Running research workflow..."):
            result = run_research_from_ui(topic, mode)
    except (EnvironmentError, ValueError) as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        logger.exception("Research execution failed from Streamlit UI: %s", exc)
        st.error("Research execution failed. Check logs for details.")
        return

    render_stats_panel(result, mode)
    if mode == "flow":
        render_flow_state(result)
    st.subheader("Agent Outputs")
    render_agent_output_section(result)
    st.subheader("Final Research Document")
    final_output = str(result.get("final_output", ""))
    st.markdown(final_output)
    st.download_button(
        "Download final document",
        final_output,
        file_name=f"research_{result.get('execution_id', 'output')}.txt",
        mime="text/plain",
    )


if __name__ == "__main__":
    render_app()
