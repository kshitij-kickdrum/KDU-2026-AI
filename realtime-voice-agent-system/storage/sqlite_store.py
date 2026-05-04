from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS customer_billing (
    customer_id TEXT PRIMARY KEY NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    plan_name TEXT NOT NULL,
    balance_usd REAL NOT NULL DEFAULT 0.0,
    due_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('current', 'overdue', 'suspended')),
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_customer_billing_email ON customer_billing(email);
CREATE INDEX IF NOT EXISTS idx_customer_billing_status ON customer_billing(status);
"""


class SQLiteStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self.connect() as connection:
            cursor = connection.execute(sql, params)
            if cursor.description:
                return [dict(row) for row in cursor.fetchall()]
            connection.commit()
            return []

    def find_customer(self, query: str) -> list[dict[str, Any]]:
        like = f"%{query}%"
        return self.execute(
            """
            SELECT customer_id, full_name, email, plan_name, balance_usd, due_date, status
            FROM customer_billing
            WHERE customer_id = ? OR email = ? OR full_name LIKE ?
            LIMIT 5
            """,
            (query.strip(), query.strip(), like),
        )

