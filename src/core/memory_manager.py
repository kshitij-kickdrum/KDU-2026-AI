from __future__ import annotations

import logging
import re
import secrets
from datetime import UTC, datetime
from typing import Any

from src.storage.database import Database
from src.utils.config import AppConfig
from src.utils.token_counter import TokenCounter

LOGGER = logging.getLogger(__name__)


class MemoryManager:
    MONEY_RE = re.compile(r"\$\s*\d+(?:,\d{3})*(?:\.\d{2})?|\b\d+(?:,\d{3})*\.\d{2}\b")
    TRANSACTION_RE = re.compile(r"\b(?:TXN|ORD|INV|ORDER|INVOICE)[-_]?[A-Z0-9-]+\b", re.I)
    DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b")
    ACCOUNT_RE = re.compile(r"\b(?:acct|account)\s*(?:number)?\s*[:#-]?\s*([A-Z0-9*]{4,})\b", re.I)
    NAME_RE = re.compile(r"\b[A-Z][a-z]+\s[A-Z][a-z]+\b")

    def __init__(self, database: Database, config: AppConfig) -> None:
        self.database = database
        self.config = config
        self.counter = TokenCounter(config.models.execution)

    @staticmethod
    def new_session_id() -> str:
        return secrets.token_urlsafe(16)

    def ensure_session(self, session_id: str | None = None) -> str:
        sid = session_id or self.new_session_id()
        row = self.database.fetch_one("SELECT session_id FROM sessions WHERE session_id = ?", (sid,))
        if row is None:
            self.database.execute(
                """
                INSERT INTO sessions (session_id, conversation_history, token_count, state)
                VALUES (?, ?, 0, 'active')
                """,
                (sid, "[]"),
            )
        return sid

    def load_session(self, session_id: str) -> dict[str, Any]:
        row = self.database.fetch_one("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        if row is None:
            self.ensure_session(session_id)
            row = self.database.fetch_one("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        assert row is not None
        return {
            "session_id": session_id,
            "conversation_history": self.database.loads(row["conversation_history"], []),
            "case_facts": self.load_case_facts(session_id),
            "token_count": int(row["token_count"]),
            "state": row["state"],
            "missing_fields": self.load_open_missing_fields(session_id),
        }

    def save_session(
        self,
        session_id: str,
        conversation_history: list[dict[str, str]],
        case_facts: dict[str, Any],
        state: str = "active",
    ) -> None:
        token_count = self.counter.count_payload(conversation_history)
        self.database.execute(
            """
            UPDATE sessions
            SET conversation_history = ?, token_count = ?, state = ?, updated_at = CURRENT_TIMESTAMP
            WHERE session_id = ?
            """,
            (self.database.dumps(conversation_history), token_count, state, session_id),
        )
        self.persist_case_facts(session_id, case_facts)

    def append_turn(
        self,
        session_id: str,
        user_query: str,
        response: str,
        state: str = "active",
    ) -> dict[str, Any]:
        session = self.load_session(session_id)
        history = session["conversation_history"]
        case_facts = self.merge_case_facts(session["case_facts"], self.extract_case_facts(user_query))
        history.extend(
            [
                {"role": "user", "content": user_query},
                {"role": "assistant", "content": response},
            ]
        )
        self.save_session(session_id, history, case_facts, state)
        return self.load_session(session_id)

    def should_compact(self, text: str, token_count: int) -> bool:
        return (
            token_count >= self.config.memory.token_threshold
            or self.counter.count_words(text) >= self.config.memory.long_document_word_threshold
        )

    def looks_like_transaction_document(self, text: str) -> bool:
        facts = self.extract_case_facts(text)
        transaction_count = len(facts["transactional"]["transaction_ids"])
        amount_count = len(facts["numerical"]["amounts"])
        date_count = len(facts["date"]["transaction_dates"])
        return transaction_count >= 2 or (transaction_count >= 1 and amount_count >= 1 and date_count >= 1)

    def compact_memory(self, session_id: str) -> dict[str, Any]:
        session = self.load_session(session_id)
        original_history = session["conversation_history"]
        original_count = self.counter.count_payload(original_history)
        facts = session["case_facts"]
        summary = self.local_summary(original_history)
        compacted_history = [
            {
                "role": "system",
                "content": f"Compacted memory summary: {summary}\nCase facts are stored separately.",
            }
        ]
        compacted_count = self.counter.count_payload(compacted_history)
        self.save_session(session_id, compacted_history, facts, session["state"])
        LOGGER.info(
            "Memory compaction: original_token_count=%s, compacted_token_count=%s, facts_extracted=%s",
            original_count,
            compacted_count,
            self.count_facts(facts),
        )
        return {
            "original_token_count": original_count,
            "compacted_token_count": compacted_count,
            "facts_extracted": self.count_facts(facts),
            "summary": summary,
        }

    def extract_case_facts(self, text: str) -> dict[str, dict[str, list[str]]]:
        amounts = sorted(set(self.MONEY_RE.findall(text)))
        transaction_ids = sorted(set(match.upper() for match in self.TRANSACTION_RE.findall(text)))
        dates = sorted(set(self.DATE_RE.findall(text)))
        account_numbers = sorted(set(self.ACCOUNT_RE.findall(text)))
        names = sorted(set(self.NAME_RE.findall(text)))
        return {
            "numerical": {"amounts": amounts},
            "transactional": {"transaction_ids": transaction_ids},
            "entity": {"person_names": names, "account_numbers": account_numbers},
            "date": {"transaction_dates": dates},
        }

    def merge_case_facts(self, existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
        merged = existing.copy()
        for fact_type, values in incoming.items():
            merged.setdefault(fact_type, {})
            for key, new_values in values.items():
                current = set(merged[fact_type].get(key, []))
                current.update(value for value in new_values if value)
                merged[fact_type][key] = sorted(current)
        return merged

    def persist_case_facts(self, session_id: str, case_facts: dict[str, Any]) -> None:
        self.database.execute("DELETE FROM case_facts WHERE session_id = ?", (session_id,))
        for fact_type, grouped in case_facts.items():
            if fact_type not in {"numerical", "transactional", "entity", "date"}:
                continue
            for fact_key, fact_value in grouped.items():
                if fact_value:
                    self.database.execute(
                        """
                        INSERT INTO case_facts (session_id, fact_type, fact_key, fact_value)
                        VALUES (?, ?, ?, ?)
                        """,
                        (session_id, fact_type, fact_key, self.database.dumps(fact_value)),
                    )

    def load_case_facts(self, session_id: str) -> dict[str, Any]:
        facts: dict[str, Any] = {}
        rows = self.database.fetch_all(
            "SELECT fact_type, fact_key, fact_value FROM case_facts WHERE session_id = ?",
            (session_id,),
        )
        for row in rows:
            facts.setdefault(row["fact_type"], {})[row["fact_key"]] = self.database.loads(
                row["fact_value"], []
            )
        return facts

    def validate_required_fields(
        self,
        session_id: str,
        operation_type: str,
        provided_fields: dict[str, Any],
    ) -> list[str]:
        row = self.database.fetch_one(
            "SELECT required_fields FROM required_fields_schema WHERE operation_type = ?",
            (operation_type,),
        )
        if row is None:
            return []
        required = self.database.loads(row["required_fields"], [])
        missing = [field for field in required if not provided_fields.get(field)]
        if missing:
            self.database.execute(
                """
                INSERT INTO missing_fields_tracking (session_id, operation_type, missing_fields)
                VALUES (?, ?, ?)
                """,
                (session_id, operation_type, self.database.dumps(missing)),
            )
            self.database.execute(
                "UPDATE sessions SET state = 'requires_user_input' WHERE session_id = ?",
                (session_id,),
            )
        return missing

    def load_open_missing_fields(self, session_id: str) -> list[str]:
        rows = self.database.fetch_all(
            """
            SELECT missing_fields FROM missing_fields_tracking
            WHERE session_id = ? AND resolved_at IS NULL
            """,
            (session_id,),
        )
        result: list[str] = []
        for row in rows:
            result.extend(self.database.loads(row["missing_fields"], []))
        return sorted(set(result))

    def local_summary(self, history: list[dict[str, str]]) -> str:
        joined = " ".join(turn.get("content", "") for turn in history)
        words = joined.split()
        return " ".join(words[:250])

    @staticmethod
    def count_facts(case_facts: dict[str, Any]) -> int:
        total = 0
        for grouped in case_facts.values():
            for value in grouped.values():
                total += len(value) if isinstance(value, list) else 1
        return total

    @staticmethod
    def utc_now() -> str:
        return datetime.now(UTC).isoformat()
