"""Sequential workflow implementation."""

from __future__ import annotations

from typing import Any

from src.memory.manager import MemoryManager
from src.utils.cost_tracker import CostTracker
from src.utils.logger import get_logger
from src.workflows.common import (
    execute_agent,
    memory_content,
    new_execution_id,
    now_seconds,
    render_template,
)

logger = get_logger(__name__)


def run_sequential(
    topic: str,
    agents: dict[str, Any],
    tasks_config: dict[str, Any],
    memory_manager: MemoryManager,
    cost_tracker: CostTracker,
) -> dict[str, Any]:
    """Run Researcher -> Fact-Checker -> Writer in fixed order."""
    execution_id = new_execution_id()
    started = now_seconds()
    research_task = tasks_config["research_task"]
    research = execute_agent(
        agents["researcher"],
        render_template(research_task["description"], topic=topic),
        research_task["expected_output"],
    )
    memory_manager.save_memory(
        "researcher", "research_task", "output", memory_content(research), execution_id
    )
    logger.info("researcher completed research_task")

    fact_task = tasks_config["fact_check_task"]
    fact = execute_agent(
        agents["fact_checker"],
        render_template(fact_task["description"], research_results=research),
        fact_task["expected_output"],
    )
    memory_manager.save_memory(
        "fact_checker",
        "fact_check_task",
        "output",
        memory_content(fact),
        execution_id,
    )
    logger.info("fact_checker completed fact_check_task")

    write_task = tasks_config["writing_task"]
    final = execute_agent(
        agents["writer"],
        render_template(write_task["description"], fact_check_details=fact),
        write_task["expected_output"],
    )
    memory_manager.save_memory(
        "writer", "writing_task", "output", memory_content(final), execution_id
    )
    logger.info("writer completed writing_task")

    duration = now_seconds() - started
    cost = cost_tracker.get_summary()
    estimated_cost = cost_tracker.estimate_cost()
    memory_manager.save_execution(
        execution_id, "sequential", duration, 1, "completed", estimated_cost
    )
    return {
        "final_output": final,
        "execution_id": execution_id,
        "duration_sec": duration,
        "cost": cost,
        "agent_outputs": {
            "researcher": research,
            "fact_checker": fact,
            "writer": final,
        },
    }
