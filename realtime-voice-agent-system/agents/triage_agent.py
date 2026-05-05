from __future__ import annotations

import re
from uuid import uuid4

from agents.base_agent import BaseAgent
from state.agent_state import AgentState, prune_message_history

VALID_INTENTS = {"billing", "technical_support", "general_inquiry"}


class TriageAgent(BaseAgent):
    agent_name = "triage_agent"

    async def classify(
        self,
        transcript: str,
        session: AgentState | None = None,
        route_to: str = "billing_agent",
    ) -> AgentState:
        session_id = session.session_id if session else str(uuid4())
        history = list(session.message_history) if session else []
        history.append({"role": "user", "content": transcript})
        response = await self.complete(
            session_id,
            [
                {
                    "role": "system",
                    "content": "Classify as billing, technical_support, or general_inquiry. Return one label.",
                },
                {"role": "user", "content": transcript},
            ],
        )
        intent = _normalize_intent(response.content) if response.status == "success" else ""
        if intent not in VALID_INTENTS:
            intent = _keyword_intent(transcript)
        state = AgentState(
            session_id=session_id,
            intent=intent,
            transcript=transcript,
            message_history=prune_message_history(history, session_id, self.monitor),
            metadata=dict(session.metadata) if session else {},
        )
        if self.monitor:
            await self.monitor.log(
                {
                    "record_type": "handoff_event",
                    "session_id": session_id,
                    "from_agent": self.agent_name,
                    "to_agent": route_to,
                    "agent_state_snapshot": state.to_dict(),
                }
            )
        return state


def _normalize_intent(text: str) -> str:
    lowered = text.strip().lower()
    match = re.search(r"billing|technical_support|general_inquiry", lowered)
    return match.group(0) if match else lowered


def _keyword_intent(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("bill", "payment", "invoice", "balance", "charge")):
        return "billing"
    if any(word in lowered for word in ("error", "bug", "login", "technical", "support")):
        return "technical_support"
    return "general_inquiry"

