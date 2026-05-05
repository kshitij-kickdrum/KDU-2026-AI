from __future__ import annotations

import re
from typing import Any


class ContextManager:
    ROUTING_RE = re.compile(r"\b\d{9}\b")
    MONEY_RE = re.compile(r"\$?\b\d+(?:,\d{3})*(?:\.\d{2})?\b")
    NAME_RE = re.compile(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b")

    def build_context_payload(
        self,
        query: str,
        target_agent: str,
        session_context: dict[str, Any],
        intent: str | None = None,
    ) -> dict[str, Any]:
        entities = self.extract_entities(query)
        parameters = self.extract_parameters(query)
        relevant_facts = self.relevant_facts_for(target_agent, session_context.get("case_facts", {}))
        missing_fields = session_context.get("missing_fields", [])
        return {
            "intent": intent or self.infer_intent_label(query),
            "target_agent": target_agent,
            "entities": entities,
            "parameters": parameters,
            "relevant_facts": relevant_facts,
            "redacted_fields": [],
            "missing_fields": missing_fields,
            "user_query_summary": query[:500],
        }

    def extract_entities(self, text: str) -> dict[str, Any]:
        names = [name for name in self.NAME_RE.findall(text) if name.lower() not in {"Update"}]
        return {"person_names": names[:5]}

    def extract_parameters(self, text: str) -> dict[str, Any]:
        parameters: dict[str, Any] = {}
        routing = self.ROUTING_RE.search(text)
        if routing:
            parameters["routing_number"] = routing.group(0)
        amounts = self.MONEY_RE.findall(text)
        if amounts:
            parameters["numbers"] = amounts[:10]
        return parameters

    def infer_intent_label(self, query: str) -> str:
        lowered = query.lower()
        if "bank" in lowered or "routing" in lowered:
            return "update_banking_details"
        if "salary" in lowered or "payroll" in lowered:
            return "get_salary"
        if "pto" in lowered or "leave" in lowered:
            return "get_pto"
        if "plan" in lowered or "steps" in lowered:
            return "generate_plan"
        return "general_query"

    def relevant_facts_for(self, target_agent: str, case_facts: dict[str, Any]) -> dict[str, Any]:
        if target_agent == "FinanceAgent":
            keys = {"numerical", "transactional", "date", "entity"}
        elif target_agent == "HRAgent":
            keys = {"entity", "date"}
        else:
            keys = set(case_facts)
        return {key: value for key, value in case_facts.items() if key in keys}

    @staticmethod
    def validate_no_history(payload: dict[str, Any]) -> None:
        forbidden = {"conversation_history", "history", "messages", "full_chat_history"}
        overlap = forbidden.intersection(payload)
        if overlap:
            raise ValueError(f"Context payload contains forbidden history keys: {sorted(overlap)}")
