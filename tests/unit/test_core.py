"""Focused unit tests."""

from __future__ import annotations

from unittest.mock import patch

import app
import pytest
import yaml
from pydantic import ValidationError

from src.agents.factory import RetryWrappedTool, build_agents
from src.config import loader
from src.config.loader import load_agents_config, validate_agents_config
from src.memory.manager import MemoryManager
from src.state.flow_state import FlowState
from src.tools.failing_tool import UnreliableResearchTool
from src.tools.retry import with_exponential_backoff
from src.ui import components, flow_state_view, history_view, stats_panel
from src.utils.cost_tracker import CostTracker
from src.utils.validation import validate_topic
from tests.fixtures.mock_llm import MockLLM
from tests.fixtures.paths import make_test_path
from tests.fixtures.sample_configs import VALID_AGENTS_CONFIG


def test_config_load_and_validation():
    path = make_test_path("agents") / "agents.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(VALID_AGENTS_CONFIG), encoding="utf-8")
    config = load_agents_config(str(path))
    assert config["researcher"]["role"] == "Senior Research Analyst"
    invalid = {"researcher": {"goal": "x", "backstory": "x", "tools": []}}
    with pytest.raises(ValueError, match="role"):
        validate_agents_config(invalid)


def test_flow_state_validation():
    state = FlowState()
    assert state.iteration_counter == 0
    assert state.fact_check_status == "pending"
    FlowState(iteration_counter=3)
    with pytest.raises(ValidationError):
        FlowState(iteration_counter=4)
    with pytest.raises(ValidationError):
        FlowState(research_results="x" * 10_001)
    with pytest.raises(ValidationError):
        FlowState(fact_check_status="bad")


def test_unreliable_tool_paths():
    tool = UnreliableResearchTool()
    with patch("src.tools.failing_tool.random.random", return_value=0.1):
        with pytest.raises(TimeoutError):
            tool._run("query")
    with patch("src.tools.failing_tool.random.random", return_value=0.9):
        assert tool._run("query").startswith("Supplemental data for:")
    with pytest.raises(ValueError):
        tool._run("x" * 501)


def test_retry_delays_and_exhaustion(caplog):
    def always_fails():
        raise TimeoutError("nope")

    with patch("src.tools.retry.time.sleep") as sleep:
        assert with_exponential_backoff(always_fails) is None
    assert [call.args[0] for call in sleep.call_args_list] == [1.0, 2.0, 4.0]
    assert "Maximum retries exceeded" in caplog.text


def test_memory_persistence():
    db_path = make_test_path("memory.db")
    first = MemoryManager(db_path)
    first.save_memory("researcher", "task", "output", "content", "exec")
    second = MemoryManager(db_path)
    assert second.load_memory("researcher", "exec")[0]["content"] == "content"
    first.close()
    second.close()


def test_cost_tracker_summary():
    tracker = CostTracker()
    tracker.record_tokens("researcher", 1000, 500)
    summary = tracker.get_summary()
    assert summary["total_tokens"] == 1500
    assert tracker.estimate_cost("gpt-3.5-turbo") > 0


def test_agent_factory_and_wrapped_tool():
    agents = build_agents(VALID_AGENTS_CONFIG, MockLLM())
    assert set(agents) == {"researcher", "fact_checker", "writer"}
    wrapped = RetryWrappedTool()
    with patch("src.agents.factory.with_exponential_backoff", return_value=None):
        assert "unavailable" in wrapped._run("query")


def test_loader_provider_env_errors(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "")
    with pytest.raises(EnvironmentError, match="SERPER_API_KEY"):
        loader.get_llm_provider()
    monkeypatch.setenv("SERPER_API_KEY", "serper")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    with pytest.raises(EnvironmentError, match="OPENAI_API_KEY"):
        loader.get_llm_provider()


def test_validate_topic():
    assert validate_topic(" AI, healthcare! ") == "AI, healthcare!"
    with pytest.raises(ValueError):
        validate_topic("")
    with pytest.raises(ValueError):
        validate_topic("<script>")


def test_ui_helpers_and_app_import():
    result = {
        "execution_id": "1234567890",
        "duration_sec": 1.25,
        "cost": {"estimated_usd": 0.01, "total_tokens": 10},
        "agent_outputs": {"researcher": "r", "fact_checker": "f", "writer": "w"},
    }
    assert components.extract_agent_outputs(result)["writer"] == "w"
    assert stats_panel.format_stats(result, "sequential")["Duration"] == "1.25s"
    assert history_view.truncate_execution_id("1234567890") == "12345678"
    rows = flow_state_view.get_flow_state_rows({"fact_check_status": "passed"})
    assert rows[0]["value"] == "passed"
    assert callable(app.render_app)


class DummyExpander:
    """Context manager used by the fake Streamlit object."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class DummyColumn:
    """Fake Streamlit column."""

    def metric(self, label, value):
        return None


class DummySidebar:
    """Fake Streamlit sidebar."""

    def subheader(self, value):
        return None

    def write(self, value):
        return None

    def toggle(self, label, value=False):
        return value


class DummyStreamlit:
    """Small fake Streamlit surface for render helper tests."""

    sidebar = DummySidebar()

    def text_input(self, label, placeholder=""):
        return "AI in healthcare"

    def radio(self, label, options, horizontal=False):
        return options[0]

    def button(self, label, type="secondary"):
        return True

    def expander(self, label, expanded=False):
        return DummyExpander()

    def markdown(self, value):
        return None

    def subheader(self, value):
        return None

    def columns(self, count):
        return [DummyColumn() for _ in range(count)]

    def caption(self, value):
        return None

    def dataframe(self, data, hide_index=True, use_container_width=True):
        return None

    def info(self, value):
        return None

    def selectbox(self, label, options, format_func=None):
        return options[0]


def test_streamlit_render_helpers(monkeypatch):
    fake = DummyStreamlit()
    monkeypatch.setattr(components, "st", fake)
    monkeypatch.setattr(stats_panel, "st", fake)
    monkeypatch.setattr(flow_state_view, "st", fake)
    monkeypatch.setattr(history_view, "st", fake)

    topic, mode, run_clicked = components.render_topic_input()
    assert (topic, mode, run_clicked) == ("AI in healthcare", "sequential", True)
    components.render_environment_status()
    components.render_agent_output_section({"final_output": "done"})
    stats_panel.render_stats_panel({"duration_sec": 0.1, "cost": {}}, "flow")
    flow_state_view.render_flow_state(
        {"state": {"fact_check_status": "passed", "iteration_counter": 1}}
    )

    manager = MemoryManager(make_test_path("history.db"))
    manager.save_execution("execution-123", "flow", 1.0, 1, "completed", 0.0)
    manager.save_memory("writer", "writing_task", "output", "done", "execution-123")
    history = history_view.load_execution_history(manager)
    assert history[0]["execution_id"] == "execution-123"
    memory = history_view.load_execution_memory(manager, "execution-123")
    assert memory[0]["agent_role"] == "writer"
    history_view.render_history(manager)
    manager.close()
