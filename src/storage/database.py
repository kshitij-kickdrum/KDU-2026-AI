from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from src.models.file_models import CostRecord, EmbeddingRecord, FileRecord


class Database:
    DISPLAY_PREFIX = {
        "pdf": "PDF",
        "image": "IMG",
        "audio": "AUD",
    }

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize_database(self) -> None:
        with self.connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS files (
                    file_id TEXT PRIMARY KEY NOT NULL,
                    display_id TEXT,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    upload_timestamp TEXT NOT NULL,
                    processing_status TEXT NOT NULL DEFAULT 'pending',
                    transcript_path TEXT NULL,
                    summary TEXT NULL,
                    key_points TEXT NULL,
                    topic_tags TEXT NULL,
                    error_message TEXT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS embeddings (
                    embedding_id TEXT PRIMARY KEY NOT NULL,
                    file_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    chunk_text TEXT NOT NULL,
                    chunk_start_char INTEGER NOT NULL,
                    chunk_end_char INTEGER NOT NULL,
                    faiss_index_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(file_id) REFERENCES files(file_id) ON DELETE CASCADE,
                    UNIQUE(file_id, chunk_index)
                );

                CREATE TABLE IF NOT EXISTS api_costs (
                    cost_id TEXT PRIMARY KEY NOT NULL,
                    file_id TEXT NULL,
                    operation_type TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL DEFAULT 0,
                    output_tokens INTEGER NOT NULL DEFAULT 0,
                    total_tokens INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT NULL,
                    FOREIGN KEY(file_id) REFERENCES files(file_id) ON DELETE SET NULL
                );

                CREATE INDEX IF NOT EXISTS idx_files_status ON files(processing_status);
                CREATE INDEX IF NOT EXISTS idx_files_type ON files(file_type);
                CREATE INDEX IF NOT EXISTS idx_files_upload_timestamp ON files(upload_timestamp DESC);

                CREATE INDEX IF NOT EXISTS idx_embeddings_file_id ON embeddings(file_id);
                CREATE INDEX IF NOT EXISTS idx_embeddings_faiss_index ON embeddings(faiss_index_id);

                CREATE INDEX IF NOT EXISTS idx_api_costs_file_id ON api_costs(file_id);
                CREATE INDEX IF NOT EXISTS idx_api_costs_operation ON api_costs(operation_type);
                CREATE INDEX IF NOT EXISTS idx_api_costs_timestamp ON api_costs(timestamp DESC);
                """
            )
            self._ensure_display_id_column(conn)
            self._backfill_display_ids(conn)

    def _ensure_display_id_column(self, conn: sqlite3.Connection) -> None:
        cols = conn.execute("PRAGMA table_info(files)").fetchall()
        col_names = {str(col["name"]) for col in cols}
        if "display_id" not in col_names:
            conn.execute("ALTER TABLE files ADD COLUMN display_id TEXT")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_files_display_id ON files(display_id)")

    def _backfill_display_ids(self, conn: sqlite3.Connection) -> None:
        rows = conn.execute(
            """
            SELECT file_id, file_type
            FROM files
            WHERE display_id IS NULL OR display_id = ''
            ORDER BY upload_timestamp ASC, created_at ASC, file_id ASC
            """
        ).fetchall()
        if not rows:
            return

        counters = self._display_counters(conn)
        for row in rows:
            file_type = row["file_type"]
            prefix = self.DISPLAY_PREFIX.get(file_type, file_type.upper()[:3])
            counters[file_type] = counters.get(file_type, 0) + 1
            display_id = f"{prefix}{counters[file_type]}"
            conn.execute(
                "UPDATE files SET display_id = ? WHERE file_id = ?",
                (display_id, row["file_id"]),
            )

    def _display_counters(self, conn: sqlite3.Connection) -> dict[str, int]:
        counters = {"pdf": 0, "image": 0, "audio": 0}
        rows = conn.execute(
            """
            SELECT file_type, display_id
            FROM files
            WHERE display_id IS NOT NULL AND display_id <> ''
            """
        ).fetchall()
        for row in rows:
            file_type = row["file_type"]
            prefix = self.DISPLAY_PREFIX.get(file_type, file_type.upper()[:3])
            display_id = str(row["display_id"])
            if not display_id.startswith(prefix):
                continue
            suffix = display_id[len(prefix) :]
            if suffix.isdigit():
                counters[file_type] = max(counters.get(file_type, 0), int(suffix))
        return counters

    def allocate_display_id(self, file_type: str) -> str:
        prefix = self.DISPLAY_PREFIX.get(file_type, file_type.upper()[:3])
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT display_id FROM files WHERE file_type = ? AND display_id IS NOT NULL",
                (file_type,),
            ).fetchall()
            max_idx = 0
            for row in rows:
                display_id = str(row["display_id"])
                if display_id.startswith(prefix):
                    suffix = display_id[len(prefix) :]
                    if suffix.isdigit():
                        max_idx = max(max_idx, int(suffix))
            return f"{prefix}{max_idx + 1}"

    def insert_file(self, record: FileRecord) -> None:
        record.validate()
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO files (
                    file_id, display_id, filename, file_type, file_path, file_size_bytes,
                    upload_timestamp, processing_status, transcript_path, summary,
                    key_points, topic_tags, error_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.file_id,
                    record.display_id,
                    record.filename,
                    record.file_type,
                    record.file_path,
                    record.file_size_bytes,
                    record.upload_timestamp,
                    record.processing_status,
                    record.transcript_path,
                    record.summary,
                    record.key_points,
                    record.topic_tags,
                    record.error_message,
                    record.created_at,
                    record.updated_at,
                ),
            )

    def update_file_status(self, file_id: str, status: str, error_message: str | None = None) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE files
                SET processing_status = ?, error_message = ?, updated_at = datetime('now')
                WHERE file_id = ?
                """,
                (status, error_message, file_id),
            )

    def update_file_results(
        self,
        file_id: str,
        transcript_path: str,
        summary: str,
        key_points: list[str],
        topic_tags: list[str],
    ) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE files
                SET transcript_path = ?, summary = ?, key_points = ?, topic_tags = ?,
                    processing_status = 'completed', error_message = NULL, updated_at = datetime('now')
                WHERE file_id = ?
                """,
                (transcript_path, summary, json.dumps(key_points), json.dumps(topic_tags), file_id),
            )

    def get_file(self, file_id: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM files WHERE file_id = ?", (file_id,)).fetchone()
            return dict(row) if row else None

    def list_files(
        self, file_type: str | None = None, status: str | None = None, name_query: str | None = None
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM files WHERE 1=1"
        params: list[Any] = []
        if file_type:
            query += " AND file_type = ?"
            params.append(file_type)
        if status:
            query += " AND processing_status = ?"
            params.append(status)
        if name_query:
            query += " AND filename LIKE ?"
            params.append(f"%{name_query}%")
        query += " ORDER BY upload_timestamp DESC"

        with self.connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def delete_file(self, file_id: str) -> None:
        with self.connection() as conn:
            conn.execute("DELETE FROM files WHERE file_id = ?", (file_id,))

    def insert_embeddings(self, records: list[EmbeddingRecord]) -> None:
        if not records:
            return
        with self.connection() as conn:
            conn.executemany(
                """
                INSERT INTO embeddings (
                    embedding_id, file_id, chunk_index, chunk_text, chunk_start_char,
                    chunk_end_char, faiss_index_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        r.embedding_id,
                        r.file_id,
                        r.chunk_index,
                        r.chunk_text,
                        r.chunk_start_char,
                        r.chunk_end_char,
                        r.faiss_index_id,
                        r.created_at,
                    )
                    for r in records
                ],
            )

    def delete_embeddings_for_file(self, file_id: str) -> None:
        with self.connection() as conn:
            conn.execute("DELETE FROM embeddings WHERE file_id = ?", (file_id,))

    def get_embeddings_by_faiss_ids(self, faiss_ids: list[int]) -> list[dict[str, Any]]:
        if not faiss_ids:
            return []
        placeholders = ",".join("?" for _ in faiss_ids)
        with self.connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM embeddings WHERE faiss_index_id IN ({placeholders})", faiss_ids
            ).fetchall()
            return [dict(r) for r in rows]

    def insert_cost(self, record: CostRecord) -> None:
        record.validate()
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO api_costs (
                    cost_id, file_id, operation_type, model_name, input_tokens,
                    output_tokens, total_tokens, cost_usd, timestamp, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.cost_id,
                    record.file_id,
                    record.operation_type,
                    record.model_name,
                    record.input_tokens,
                    record.output_tokens,
                    record.total_tokens,
                    record.cost_usd,
                    record.timestamp,
                    record.metadata,
                ),
            )

    def get_cost_rows(self, file_id: str | None = None) -> list[dict[str, Any]]:
        with self.connection() as conn:
            if file_id:
                rows = conn.execute(
                    "SELECT * FROM api_costs WHERE file_id = ? ORDER BY timestamp DESC", (file_id,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM api_costs ORDER BY timestamp DESC").fetchall()
            return [dict(r) for r in rows]

    def get_cost_breakdown(self, file_id: str | None = None) -> dict[str, Any]:
        rows = self.get_cost_rows(file_id)
        by_operation: dict[str, float] = {"vision": 0.0, "llm": 0.0, "embedding": 0.0}
        total_cost = 0.0
        total_tokens = 0
        for row in rows:
            total_cost += float(row["cost_usd"])
            total_tokens += int(row["total_tokens"])
            by_operation[row["operation_type"]] = by_operation.get(row["operation_type"], 0.0) + float(
                row["cost_usd"]
            )
        return {
            "total_cost_usd": round(total_cost, 8),
            "total_tokens": total_tokens,
            "by_operation": by_operation,
            "rows": rows,
        }

    def get_cost_per_file(self) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    f.file_id,
                    f.filename,
                    COALESCE(SUM(c.cost_usd), 0) AS total_cost_usd,
                    COALESCE(SUM(c.total_tokens), 0) AS total_tokens
                FROM files f
                LEFT JOIN api_costs c ON f.file_id = c.file_id
                GROUP BY f.file_id, f.filename
                ORDER BY total_cost_usd DESC
                """
            ).fetchall()
            return [dict(r) for r in rows]

    def get_daily_costs(self) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    substr(timestamp, 1, 10) AS day,
                    SUM(cost_usd) AS total_cost_usd,
                    SUM(total_tokens) AS total_tokens
                FROM api_costs
                GROUP BY substr(timestamp, 1, 10)
                ORDER BY day ASC
                """
            ).fetchall()
            return [dict(r) for r in rows]
