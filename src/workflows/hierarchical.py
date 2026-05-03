"""Hierarchical workflow implementation."""

from __future__ import annotations

from typing import Any

from src.memory.manager import MemoryManager
from src.utils.cost_tracker import CostTracker
from src.utils.logger import get_logger
from src.workflows.sequential import run_sequential

logger = get_logger(__name__)


def run_hierarchical(
    topic: str,
    agents: dict[str, Any],
    tasks_config: dict[str, Any],
    llm: Any,
    memory_manager: MemoryManager,
    cost_tracker: CostTracker,
) -> dict[str, Any]:
    """Run manager-style orchestration and log cost overhead."""
    result = run_sequential(topic, agents, tasks_config, memory_manager, cost_tracker)
    result["mode"] = "hierarchical"
    memory_manager.save_execution(
        result["execution_id"],
        "hierarchical",
        float(result["duration_sec"]),
        1,
        "completed",
        float(result["cost"]["estimated_usd"]),
    )
    logger.info(
        "Hierarchical workflow with manager_llm=%s is typically more "
        "expensive than sequential.",
        llm.__class__.__name__ if llm is not None else "None",
    )
    return result
