from __future__ import annotations

import json
import re
import secrets
from datetime import UTC, datetime
from typing import Any

from src.agents.base_agent import BaseSDKAgent
from src.core.exceptions import AgentKitError
from src.storage.database import Database
from src.utils.config import AppConfig


class PlannerAgent(BaseSDKAgent):
    def __init__(self, config: AppConfig, database: Database, session_id: str) -> None:
        self.database = database
        self.session_id = session_id
        super().__init__(
            name="PlannerAgent",
            instructions=config.prompts["planner"],
            model=config.models.planner,
            tools=[],
            config=config,
        )

    def generate_plan(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        last_output = ""
        for attempt in range(3):
            prompt = (
                f"Create a valid JSON execution plan for this task: {task}\n"
                f"Use session_id: {self.session_id}\n"
                "Return JSON only."
            )
            if attempt:
                prompt += "\nThe previous output was invalid JSON. Return corrected JSON only."
            try:
                last_output = self.run(prompt, context)
            except AgentKitError:
                break
            try:
                plan = self._parse_json(last_output)
                self._validate_plan(plan)
                self.persist_plan(plan)
                return plan
            except (json.JSONDecodeError, ValueError):
                continue
        plan = self._fallback_plan(task)
        self.persist_plan(plan)
        return plan

    def persist_plan(self, plan: dict[str, Any]) -> None:
        self.database.execute(
            """
            INSERT OR IGNORE INTO sessions (session_id, conversation_history, token_count, state)
            VALUES (?, '[]', 0, 'active')
            """,
            (self.session_id,),
        )
        self.database.execute(
            """
            INSERT INTO execution_plans (plan_id, session_id, plan_json, status)
            VALUES (?, ?, ?, 'pending')
            ON CONFLICT(plan_id) DO UPDATE SET plan_json = excluded.plan_json
            """,
            (plan["plan_id"], self.session_id, self.database.dumps(plan)),
        )
        for step in plan.get("steps", []):
            self.database.execute(
                """
                INSERT INTO execution_steps (
                    step_id, plan_id, step_order, description, action_type,
                    parameters, depends_on, expected_output, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(step_id) DO UPDATE SET
                    description = excluded.description,
                    parameters = excluded.parameters,
                    depends_on = excluded.depends_on,
                    expected_output = excluded.expected_output
                """,
                (
                    step["step_id"],
                    plan["plan_id"],
                    int(step["step_order"]),
                    step["description"],
                    step["action_type"],
                    self.database.dumps(step.get("parameters", {})),
                    self.database.dumps(step.get("depends_on", [])),
                    step["expected_output"],
                    step.get("status", "pending"),
                ),
            )

    @staticmethod
    def _parse_json(output: str) -> dict[str, Any]:
        cleaned = output.strip()
        match = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.S)
        if match:
            cleaned = match.group(1).strip()
        elif "{" in cleaned and "}" in cleaned:
            cleaned = cleaned[cleaned.find("{") : cleaned.rfind("}") + 1]
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ValueError("Plan must be a JSON object.")
        return parsed

    @staticmethod
    def _validate_plan(plan: dict[str, Any]) -> None:
        for key in ["plan_id", "session_id", "steps", "metadata"]:
            if key not in plan:
                raise ValueError(f"Missing plan key: {key}")
        if not isinstance(plan["steps"], list) or not plan["steps"]:
            raise ValueError("Plan must contain at least one step.")
        required = {"step_id", "step_order", "description", "action_type", "parameters", "expected_output"}
        for step in plan["steps"]:
            missing = required.difference(step)
            if missing:
                raise ValueError(f"Step is missing keys: {sorted(missing)}")

    def _fallback_plan(self, task: str) -> dict[str, Any]:
        plan_id = f"plan_{secrets.token_urlsafe(8)}"
        step_1 = f"{plan_id}_step_1"
        step_2 = f"{plan_id}_step_2"
        step_3 = f"{plan_id}_step_3"
        return {
            "plan_id": plan_id,
            "session_id": self.session_id,
            "created_at": datetime.now(UTC).isoformat(),
            "steps": [
                {
                    "step_id": step_1,
                    "step_order": 0,
                    "description": "Collect available case facts for reconciliation.",
                    "action_type": "data_transform",
                    "agent_or_tool": "case_facts",
                    "parameters": {"task": task},
                    "depends_on": [],
                    "expected_output": "Relevant transaction IDs, amounts, dates, and entities.",
                    "validation": {"requires_case_facts": True},
                    "status": "pending",
                    "actual_output": None,
                    "error": None,
                },
                {
                    "step_id": step_2,
                    "step_order": 1,
                    "description": "Compare transaction facts and identify reconciliation notes.",
                    "action_type": "data_transform",
                    "agent_or_tool": "ExecutorAgent",
                    "parameters": {"analysis_type": "reconciliation"},
                    "depends_on": [step_1],
                    "expected_output": "Short reconciliation analysis.",
                    "validation": {"format": "text"},
                    "status": "pending",
                    "actual_output": None,
                    "error": None,
                },
                {
                    "step_id": step_3,
                    "step_order": 2,
                    "description": "Generate a short final reconciliation report.",
                    "action_type": "data_transform",
                    "agent_or_tool": "ExecutorAgent",
                    "parameters": {"output": "short_report"},
                    "depends_on": [step_2],
                    "expected_output": "Concise reconciliation report.",
                    "validation": {"max_paragraphs": 3},
                    "status": "pending",
                    "actual_output": None,
                    "error": None,
                },
            ],
            "metadata": {
                "planner_model": self.model,
                "estimated_duration": 30,
                "complexity": "moderate",
                "fallback_used": True,
            },
        }
