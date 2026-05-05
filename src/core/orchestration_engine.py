from __future__ import annotations

import logging
from typing import Any

from src.agents.coordinator_agent import CoordinatorAgent
from src.agents.executor_agent import ExecutorAgent
from src.agents.loop_agent import LoopDetectionAgent
from src.agents.planner_agent import PlannerAgent
from src.core.circuit_breaker import FALLBACK_RESPONSE, CircuitBreaker
from src.core.context_manager import ContextManager
from src.core.exceptions import (
    CircuitBreakerOpenError,
    MissingAPIKeyError,
    ProviderConnectionError,
    SDKUnavailableError,
    TokenBudgetError,
)
from src.core.memory_manager import MemoryManager
from src.storage.database import Database
from src.tools.runtime import ToolRuntime
from src.utils.config import AppConfig, load_config
from src.utils.logger import configure_logging

LOGGER = logging.getLogger(__name__)


class OrchestrationEngine:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or load_config()
        configure_logging(self.config)
        self.database = Database(self.config.database_path)
        self.database.initialize()
        self.circuit_breaker = CircuitBreaker(self.database, self.config.circuit_breaker)
        self.memory = MemoryManager(self.database, self.config)
        self.context_manager = ContextManager()
        self.runtime = ToolRuntime(self.database, self.circuit_breaker)

    def process_query(self, query: str, session_id: str | None = None) -> dict[str, Any]:
        sid = self.memory.ensure_session(session_id)
        try:
            session = self.memory.load_session(sid)
            token_count = self.memory.counter.count_text(query)
            if self.memory.should_compact(query, token_count) or self.memory.looks_like_transaction_document(
                query
            ):
                return self._ingest_long_document(sid, query)

            provided_fields = self.context_manager.extract_parameters(query)
            missing_fields = self.memory.validate_required_fields(
                sid,
                self.context_manager.infer_intent_label(query),
                provided_fields,
            )
            session = self.memory.load_session(sid)
            response = self._route_query(query, sid, session)
            state = "requires_user_input" if missing_fields else session["state"]
            updated_session = self.memory.append_turn(sid, query, response, state)
            if updated_session["token_count"] >= self.config.memory.token_threshold:
                compaction = self.memory.compact_memory(sid)
            else:
                compaction = None
            return self._response(
                session_id=sid,
                response=response,
                session=updated_session,
                compaction=compaction,
            )
        except CircuitBreakerOpenError:
            session = self.memory.append_turn(sid, query, FALLBACK_RESPONSE, "active")
            return self._response(session_id=sid, response=FALLBACK_RESPONSE, session=session)
        except SDKUnavailableError as exc:
            LOGGER.error("SDK unavailable: %s", exc)
            session = self.memory.load_session(sid)
            return self._response(
                session_id=sid,
                response=str(exc),
                session=session,
                error="sdk_unavailable",
            )
        except MissingAPIKeyError as exc:
            LOGGER.error("OpenAI API key missing: %s", exc)
            session = self.memory.load_session(sid)
            return self._response(
                session_id=sid,
                response=str(exc),
                session=session,
                error="missing_openai_api_key",
            )
        except ProviderConnectionError as exc:
            LOGGER.error("LLM provider connection failed: %s", exc)
            session = self.memory.load_session(sid)
            return self._response(
                session_id=sid,
                response=str(exc),
                session=session,
                error="provider_connection_error",
            )
        except TokenBudgetError as exc:
            LOGGER.warning("Token budget exceeded: %s", exc)
            session = self.memory.load_session(sid)
            return self._response(
                session_id=sid,
                response=(
                    "That input exceeds the configured token budget. "
                    "Please provide a smaller input or ingest it as a document."
                ),
                session=session,
                error="token_budget_exceeded",
            )
        except Exception as exc:
            LOGGER.exception("Unhandled orchestration error")
            session = self.memory.load_session(sid)
            return self._response(
                session_id=sid,
                response="I hit an internal error while processing that request.",
                session=session,
                error=str(exc),
            )

    def _route_query(self, query: str, session_id: str, session: dict[str, Any]) -> str:
        lowered = query.lower()
        if "count the active users" in lowered or "active users" in lowered:
            return LoopDetectionAgent(self.config, self.runtime, session_id).run_circuit_breaker_demo()
        if query.strip().lower().startswith("/plan") or "planner-executor" in lowered:
            task = query.replace("/plan", "", 1).strip()
            return self._run_planner_executor(task or query, session_id, session)
        coordinator = CoordinatorAgent(
            self.config,
            self.runtime,
            self.database,
            self.context_manager,
            session_id,
            session,
        )
        coordinator_context = {
            "session_id": session_id,
            "case_facts": session["case_facts"],
            "missing_fields": session.get("missing_fields", []),
            "note": "Do not pass full conversation history during delegation.",
        }
        return coordinator.run(query, coordinator_context)

    def _run_planner_executor(
        self,
        task: str,
        session_id: str,
        session: dict[str, Any],
    ) -> str:
        context_payload = {
            "session_id": session_id,
            "case_facts": session["case_facts"],
            "planning_context": "Use available case facts and persist execution results.",
        }
        planner = PlannerAgent(self.config, self.database, session_id)
        plan = planner.generate_plan(task, context_payload)
        executor = ExecutorAgent(self.config, self.database, session_id)
        result = executor.execute_plan(plan, context_payload | {"plan": plan})
        return self.database.dumps({"plan": plan, "execution": result})

    def _ingest_long_document(self, session_id: str, document: str) -> dict[str, Any]:
        session = self.memory.load_session(session_id)
        facts = self.memory.extract_case_facts(document)
        merged = self.memory.merge_case_facts(session["case_facts"], facts)
        response = (
            "Transaction document ingested. I extracted and stored transaction IDs, amounts, "
            "dates, and entities before any agent run, so future calls can use compact context "
            "instead of resending the document."
        )
        history = session["conversation_history"]
        history.extend(
            [
                {"role": "user", "content": "[Long document ingested and compacted into case facts]"},
                {"role": "assistant", "content": response},
            ]
        )
        self.memory.save_session(session_id, history, merged, session["state"])
        compaction = self.memory.compact_memory(session_id)
        return self._response(
            session_id=session_id,
            response=response,
            session=self.memory.load_session(session_id),
            compaction=compaction,
        )

    @staticmethod
    def _response(
        *,
        session_id: str,
        response: str,
        session: dict[str, Any],
        compaction: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "response": response,
            "state": session["state"],
            "token_count": session["token_count"],
            "case_facts": session["case_facts"],
            "missing_fields": session.get("missing_fields", []),
            "compaction": compaction,
            "error": error,
        }
