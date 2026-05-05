from __future__ import annotations

import json

from agents.base_agent import BaseAgent, trim_words
from agents.db_agent import AgentResult


class ConsensusAgent(BaseAgent):
    agent_name = "consensus_agent"

    async def aggregate(
        self,
        db_result: AgentResult,
        vector_result: AgentResult,
        session_id: str,
    ) -> str:
        db_ok = db_result.status == "success"
        vector_ok = vector_result.status == "success"
        facts = {
            "database": db_result.data if db_ok else {"unavailable": db_result.error},
            "knowledge_base": vector_result.data if vector_ok else {"unavailable": vector_result.error},
        }
        response = await self.complete(
            session_id,
            [
                {
                    "role": "system",
                    "content": "Synthesize only from provided JSON. Limit to 200 words. Disclose unavailable sources.",
                },
                {"role": "user", "content": json.dumps(facts, ensure_ascii=False)},
            ],
        )
        if response.status == "success" and response.content.strip():
            text = trim_words(response.content, 200)
        else:
            text = _fallback_consensus(db_result, vector_result)
        if self.monitor:
            await self.monitor.log(
                {
                    "record_type": "consensus_event",
                    "session_id": session_id,
                    "db_agent_status": "success" if db_ok else "failure",
                    "vector_agent_status": "success" if vector_ok else "failure",
                    "response_word_count": len(text.split()),
                }
            )
        return text


def _fallback_consensus(db_result: AgentResult, vector_result: AgentResult) -> str:
    parts = []
    if db_result.status == "success":
        rows = (db_result.data or {}).get("rows", [])
        if rows:
            row = rows[0]
            parts.append(
                f"Account {row.get('customer_id')} is on {row.get('plan_name')} with "
                f"a balance of ${row.get('balance_usd')} due {row.get('due_date')}."
            )
        else:
            parts.append("I did not find a matching billing account.")
    else:
        parts.append("The billing database was unavailable.")
    if vector_result.status == "success":
        matches = (vector_result.data or {}).get("matches", [])
        if matches:
            parts.append(f"Relevant guidance: {matches[0].get('content_preview', '')}")
    else:
        parts.append("The knowledge base was unavailable.")
    return trim_words(" ".join(parts), 200)

