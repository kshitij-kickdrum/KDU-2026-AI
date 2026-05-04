"""Workflow integration tests with deterministic agents."""

from __future__ import annotations

from src.agents.factory import build_agents
from src.memory.manager import MemoryManager
from src.utils.cost_tracker import CostTracker
from src.workflows.flow import run_flow
from src.workflows.hierarchical import run_hierarchical
from src.workflows.sequential import run_sequential
from tests.fixtures.mock_llm import MockLLM
from tests.fixtures.paths import make_test_path
from tests.fixtures.sample_configs import VALID_AGENTS_CONFIG, VALID_TASKS_CONFIG


def test_sequential_workflow():
    manager = MemoryManager(make_test_path("seq.db"))
    agents = build_agents(VALID_AGENTS_CONFIG, MockLLM())
    result = run_sequential("AI", agents, VALID_TASKS_CONFIG, manager, CostTracker())
    assert result["final_output"]
    assert manager.load_memory("writer", result["execution_id"])
    manager.close()


def test_hierarchical_workflow_logs_cost(caplog):
    manager = MemoryManager(make_test_path("hier.db"))
    llm = MockLLM()
    agents = build_agents(VALID_AGENTS_CONFIG, llm)
    result = run_hierarchical(
        "AI", agents, VALID_TASKS_CONFIG, llm, manager, CostTracker()
    )
    assert result["final_output"]
    assert "more expensive than sequential" in caplog.text
    manager.close()


def test_flow_retries_then_passes():
    manager = MemoryManager(make_test_path("flow_pass.db"))
    agents = build_agents(VALID_AGENTS_CONFIG, MockLLM(["failed", "failed", "passed"]))
    result = run_flow("AI", agents, VALID_TASKS_CONFIG, manager, CostTracker())
    assert result["status"] == "completed"
    assert result["iterations_used"] == 3
    manager.close()


def test_flow_terminates_at_three(caplog):
    manager = MemoryManager(make_test_path("flow_stop.db"))
    agents = build_agents(VALID_AGENTS_CONFIG, MockLLM(["failed", "failed", "failed"]))
    result = run_flow("AI", agents, VALID_TASKS_CONFIG, manager, CostTracker())
    assert result["status"] == "terminated"
    assert result["iterations_used"] == 3
    assert "Max iteration limit reached" in caplog.text
    manager.close()
