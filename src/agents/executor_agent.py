from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from src.agents.base_agent import BaseSDKAgent
from src.storage.database import Database
from src.utils.config import AppConfig

LOGGER = logging.getLogger(__name__)


class ExecutorAgent(BaseSDKAgent):
    def __init__(self, config: AppConfig, database: Database, session_id: str) -> None:
        self.database = database
        self.session_id = session_id
        super().__init__(
            name="ExecutorAgent",
            instructions=config.prompts["executor"],
            model=config.models.executor,
            tools=[],
            config=config,
        )

    def execute_plan(self, plan: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
        plan_id = plan["plan_id"]
        self.database.execute(
            "UPDATE execution_plans SET status = 'executing' WHERE plan_id = ?",
            (plan_id,),
        )
        results: list[dict[str, Any]] = []
        completed = self._completed_step_ids(plan_id)
        for step in sorted(plan["steps"], key=lambda item: int(item["step_order"])):
            if step["step_id"] in completed:
                results.append({"step_id": step["step_id"], "status": "skipped"})
                continue
            missing_dependencies = [
                dep for dep in step.get("depends_on", []) if dep not in completed
            ]
            if missing_dependencies:
                self._mark_step(step["step_id"], "skipped", f"Missing dependencies: {missing_dependencies}")
                results.append(
                    {
                        "step_id": step["step_id"],
                        "status": "skipped",
                        "error": f"Missing dependencies: {missing_dependencies}",
                    }
                )
                continue
            try:
                self._mark_step(step["step_id"], "executing", None)
                if plan.get("metadata", {}).get("fallback_used"):
                    output = self._execute_fallback_step(step, context or {})
                else:
                    output = self.run(
                        (
                            "Execute this plan step and return only the step result. "
                            "The orchestration engine has already verified dependencies.\n"
                            f"{step}"
                        ),
                        context,
                    )
                self._mark_step(step["step_id"], "completed", output)
                completed.add(step["step_id"])
                results.append({"step_id": step["step_id"], "status": "completed", "output": output})
            except Exception as exc:
                LOGGER.exception("Execution step failed: step_id=%s", step["step_id"])
                self._mark_step(step["step_id"], "failed", str(exc))
                self.database.execute(
                    "UPDATE execution_plans SET status = 'failed' WHERE plan_id = ?",
                    (plan_id,),
                )
                return {"plan_id": plan_id, "status": "failed", "results": results, "error": str(exc)}
        self.database.execute(
            "UPDATE execution_plans SET status = 'completed' WHERE plan_id = ?",
            (plan_id,),
        )
        return {"plan_id": plan_id, "status": "completed", "results": results}

    def _completed_step_ids(self, plan_id: str) -> set[str]:
        rows = self.database.fetch_all(
            "SELECT step_id FROM execution_steps WHERE plan_id = ? AND status = 'completed'",
            (plan_id,),
        )
        return {row["step_id"] for row in rows}

    def _mark_step(self, step_id: str, status: str, output: str | None) -> None:
        self.database.execute(
            """
            UPDATE execution_steps
            SET status = ?, actual_output = ?, executed_at = ?
            WHERE step_id = ?
            """,
            (status, output, datetime.now(UTC).isoformat(), step_id),
        )

    def _execute_fallback_step(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        case_facts = context.get("case_facts", {})
        transactions = case_facts.get("transactional", {}).get("transaction_ids", [])
        amounts = case_facts.get("numerical", {}).get("amounts", [])
        dates = case_facts.get("date", {}).get("transaction_dates", [])
        people = case_facts.get("entity", {}).get("person_names", [])

        order = int(step["step_order"])
        if order == 0:
            return (
                "Collected stored case facts for reconciliation. "
                f"Transaction IDs: {', '.join(transactions) or 'none'}. "
                f"Amounts: {', '.join(amounts) or 'none'}. "
                f"Dates: {', '.join(dates) or 'none'}. "
                f"Entities: {', '.join(people) or 'none'}."
            )
        if order == 1:
            return (
                "Compared transaction facts. "
                f"Found {len(transactions)} transaction references, {len(amounts)} amounts, "
                f"and {len(dates)} dates available for reconciliation."
            )
        return (
            "Reconciliation report: stored transaction data is available for review. "
            f"Transactions: {', '.join(transactions) or 'none recorded'}. "
            f"Amounts: {', '.join(amounts) or 'none recorded'}. "
            f"Dates: {', '.join(dates) or 'none recorded'}."
        )
