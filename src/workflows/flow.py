"""CrewAI-style event-driven flow with iteration guard."""

from __future__ import annotations

from typing import Any


class Flow:
    """Local Flow base for deterministic Streamlit execution."""


def start() -> Any:
    """Local no-op start decorator."""
    return lambda func: func


def listen(_: Any) -> Any:
    """Local no-op listen decorator."""
    return lambda func: func


def router(_: Any) -> Any:
    """Local no-op router decorator."""
    return lambda func: func

from src.memory.manager import MemoryManager
from src.state.flow_state import FlowState
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


class ResearchFlow(Flow):
    """Flow that retries research until fact-check passes or three cycles run."""

    def __init__(
        self,
        topic: str,
        agents: dict[str, Any],
        tasks_config: dict[str, Any],
        memory_manager: MemoryManager,
        cost_tracker: CostTracker,
    ) -> None:
        """Initialize flow dependencies."""
        super().__init__()
        self.topic = topic
        self.agents = agents
        self.tasks_config = tasks_config
        self.memory_manager = memory_manager
        self.cost_tracker = cost_tracker
        self.execution_id = new_execution_id()
        self.state = FlowState()
        self.started = now_seconds()

    @start()
    def run_research(self) -> str:
        """Run the Researcher and update state."""
        task = self.tasks_config["research_task"]
        output = execute_agent(
            self.agents["researcher"],
            render_template(task["description"], topic=self.topic),
            task["expected_output"],
        )
        self.state = self.state.updated(
            research_results=output,
            iteration_counter=self.state.iteration_counter + 1,
        )
        self.memory_manager.save_memory(
            "researcher",
            "research_task",
            "output",
            memory_content(output),
            self.execution_id,
        )
        logger.info(
            "Flow state transition: research iteration %s",
            self.state.iteration_counter,
        )
        return output

    @listen(run_research)
    def run_fact_check(self, research_results: str | None = None) -> str:
        """Run the Fact-Checker and update status/details."""
        task = self.tasks_config["fact_check_task"]
        details = execute_agent(
            self.agents["fact_checker"],
            render_template(
                task["description"],
                research_results=research_results or self.state.research_results or "",
            ),
            task["expected_output"],
        )
        lowered = details.lower()
        status = (
            "failed"
            if "failed" in lowered and "passed" not in lowered
            else "passed"
        )
        self.state = self.state.updated(
            fact_check_status=status,
            fact_check_details=details,
        )
        self.memory_manager.save_memory(
            "fact_checker",
            "fact_check_task",
            "output",
            memory_content(details),
            self.execution_id,
        )
        logger.info("Flow state transition: fact_check_status=%s", status)
        return details

    @router(run_fact_check)
    def route_after_fact_check(self) -> str:
        """Return write when passed or at max iterations, otherwise retry."""
        if (
            self.state.fact_check_status == "passed"
            or self.state.iteration_counter >= 3
        ):
            return "write"
        return "retry"

    @listen("write")
    def run_writer(self) -> str:
        """Run the Writer, or return partial output at max iteration failure."""
        if (
            self.state.fact_check_status != "passed"
            and self.state.iteration_counter >= 3
        ):
            logger.warning(
                "Max iteration limit reached; returning partial flow results"
            )
            partial = self.state.research_results or self.state.fact_check_details or ""
            self.state = self.state.updated(final_output=partial)
            return partial
        task = self.tasks_config["writing_task"]
        output = execute_agent(
            self.agents["writer"],
            render_template(
                task["description"],
                fact_check_details=self.state.fact_check_details or "",
            ),
            task["expected_output"],
        )
        self.state = self.state.updated(final_output=output)
        self.memory_manager.save_memory(
            "writer",
            "writing_task",
            "output",
            memory_content(output),
            self.execution_id,
        )
        logger.info("Flow state transition: writer completed")
        return output

    @listen("retry")
    def handle_retry(self) -> str:
        """Log retry or termination state."""
        if self.state.iteration_counter < 3:
            logger.info("Flow state transition: retrying research")
            return self.state.research_results or ""
        logger.warning(
            "Max iteration limit reached; terminating flow with partial results"
        )
        return self.state.research_results or ""

    def kickoff(self) -> dict[str, Any]:
        """Execute the flow in a deterministic local loop."""
        final = ""
        while self.state.iteration_counter < 3:
            research = self.run_research()
            self.run_fact_check(research)
            if self.route_after_fact_check() == "write":
                final = self.run_writer()
                break
            self.handle_retry()
        if not final:
            logger.warning(
                "Max iteration limit reached; terminating flow with partial results"
            )
            final = self.state.research_results or ""
            self.state = self.state.updated(final_output=final)
        duration = now_seconds() - self.started
        status = (
            "completed"
            if self.state.fact_check_status == "passed"
            else "terminated"
        )
        cost = self.cost_tracker.get_summary()
        self.memory_manager.save_execution(
            self.execution_id,
            "flow",
            duration,
            self.state.iteration_counter,
            status,
            self.cost_tracker.estimate_cost(),
        )
        return {
            "final_output": final,
            "execution_id": self.execution_id,
            "duration_sec": duration,
            "iterations_used": self.state.iteration_counter,
            "status": status,
            "state": self.state.model_dump(mode="json"),
            "cost": cost,
        }


def run_flow(
    topic: str,
    agents: dict[str, Any],
    tasks_config: dict[str, Any],
    memory_manager: MemoryManager,
    cost_tracker: CostTracker,
) -> dict[str, Any]:
    """Run the ResearchFlow."""
    return ResearchFlow(
        topic, agents, tasks_config, memory_manager, cost_tracker
    ).kickoff()
