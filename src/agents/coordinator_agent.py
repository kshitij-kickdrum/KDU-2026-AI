from __future__ import annotations

import logging
from typing import Any

from src.agents.base_agent import BaseSDKAgent
from src.agents.finance_agent import FinanceAgent
from src.agents.hr_agent import HRAgent
from src.agents.sdk import load_agents_sdk
from src.core.context_manager import ContextManager
from src.storage.database import Database
from src.tools.runtime import ToolRuntime
from src.utils.config import AppConfig

LOGGER = logging.getLogger(__name__)


class CoordinatorAgent(BaseSDKAgent):
    def __init__(
        self,
        config: AppConfig,
        runtime: ToolRuntime,
        database: Database,
        context_manager: ContextManager,
        session_id: str,
        session_context: dict[str, Any],
    ) -> None:
        self.database = database
        self.context_manager = context_manager
        self.session_id = session_id
        self.session_context = session_context
        self.runtime = runtime
        self.delegation_order = 0
        super().__init__(
            name="CoordinatorAgent",
            instructions=config.prompts["coordinator"],
            model=config.models.coordinator,
            tools=self._create_delegation_tools(config),
            config=config,
        )

    def _create_delegation_tools(self, config: AppConfig) -> list[Any]:
        _, _, function_tool, _ = load_agents_sdk()

        @function_tool
        def delegate_to_finance(task: str, intent: str | None = None) -> str:
            """Delegate a finance, payroll, salary, banking, account, or transaction task."""
            payload = self.context_manager.build_context_payload(
                task,
                "FinanceAgent",
                self.session_context,
                intent=intent,
            )
            self.context_manager.validate_no_history(payload)
            response = FinanceAgent(config, self.runtime, self.session_id).run(task, payload)
            self._log_delegation(task, "FinanceAgent", payload, response)
            return response

        @function_tool
        def delegate_to_hr(task: str, intent: str | None = None) -> str:
            """Delegate an HR, PTO, leave, benefits, employee, or personnel task."""
            payload = self.context_manager.build_context_payload(
                task,
                "HRAgent",
                self.session_context,
                intent=intent,
            )
            self.context_manager.validate_no_history(payload)
            response = HRAgent(config, self.runtime, self.session_id).run(task, payload)
            self._log_delegation(task, "HRAgent", payload, response)
            return response

        @function_tool
        def analyze_query(task: str) -> str:
            """Analyze a user query and describe which specialists may be needed."""
            return (
                "Use FinanceAgent for salary, payroll, compensation, banking, accounts, "
                "or transactions. Use HRAgent for PTO, leave, benefits, employee records, "
                "or personnel questions. Use both when the request spans both domains."
            )

        return [delegate_to_finance, delegate_to_hr, analyze_query]

    def _log_delegation(
        self,
        coordinator_query: str,
        sub_agent_name: str,
        context_payload: dict[str, Any],
        sub_agent_response: str,
    ) -> None:
        self.delegation_order += 1
        self.database.execute(
            """
            INSERT INTO delegation_logs (
                session_id, coordinator_query, sub_agent_name, delegation_order,
                context_payload, sub_agent_response
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                self.session_id,
                coordinator_query,
                sub_agent_name,
                self.delegation_order,
                self.database.dumps(context_payload),
                sub_agent_response,
            ),
        )
        LOGGER.info(
            "Delegated query to %s order=%s session_id=%s",
            sub_agent_name,
            self.delegation_order,
            self.session_id,
        )
