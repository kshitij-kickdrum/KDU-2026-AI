"""SQLite-backed memory persistence."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class MemoryManager:
    """Persist agent memory and execution history in SQLite."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        """Open or create the database and initialize tables."""
        root = Path(__file__).resolve().parents[2]
        self.db_path = Path(db_path) if db_path else root / "data" / "memory.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.initialize_db()

    def initialize_db(self) -> None:
        """Create required tables and indexes."""
        with self.connection:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_role VARCHAR(50) NOT NULL,
                    task_id VARCHAR(100) NOT NULL,
                    memory_type VARCHAR(30) NOT NULL,
                    content TEXT NOT NULL,
                    execution_id VARCHAR(36) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_history (
                    execution_id VARCHAR(36) PRIMARY KEY,
                    orchestration_mode VARCHAR(20) NOT NULL,
                    total_duration_sec INTEGER NOT NULL,
                    iterations_used INTEGER DEFAULT 1,
                    final_status VARCHAR(20) NOT NULL,
                    cost_estimate_usd DECIMAL(10,4),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            for column in ("agent_role", "task_id", "execution_id"):
                self.connection.execute(
                    f"CREATE INDEX IF NOT EXISTS idx_agent_memory_{column} "
                    f"ON agent_memory({column})"
                )

    def save_memory(
        self,
        agent_role: str,
        task_id: str,
        memory_type: str,
        content: str,
        execution_id: str,
    ) -> None:
        """Insert a memory row and commit the transaction."""
        self.connection.execute(
            """
            INSERT INTO agent_memory
                (agent_role, task_id, memory_type, content, execution_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (agent_role, task_id, memory_type, content, execution_id),
        )
        self.connection.commit()

    def load_memory(
        self, agent_role: str, execution_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Load memory for an agent role and optional execution id."""
        if execution_id:
            rows = self.connection.execute(
                "SELECT * FROM agent_memory WHERE agent_role = ? "
                "AND execution_id = ? ORDER BY id",
                (agent_role, execution_id),
            ).fetchall()
        else:
            rows = self.connection.execute(
                "SELECT * FROM agent_memory WHERE agent_role = ? ORDER BY id",
                (agent_role,),
            ).fetchall()
        return [dict(row) for row in rows]

    def save_execution(
        self,
        execution_id: str,
        orchestration_mode: str,
        total_duration_sec: float,
        iterations_used: int,
        final_status: str,
        cost_estimate_usd: float | None,
    ) -> None:
        """Save an execution summary."""
        with self.connection:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO execution_history
                    (execution_id, orchestration_mode, total_duration_sec,
                     iterations_used, final_status, cost_estimate_usd)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    execution_id,
                    orchestration_mode,
                    int(total_duration_sec),
                    iterations_used,
                    final_status,
                    cost_estimate_usd,
                ),
            )

    def close(self) -> None:
        """Close the database connection."""
        self.connection.close()
