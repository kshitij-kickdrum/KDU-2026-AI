from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any, cast


class Database:
    def __init__(self, path: Path, schema_path: Path | None = None) -> None:
        self.path = path
        self.schema_path = schema_path or Path(__file__).with_name("schema.sql")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(self.schema_path.read_text(encoding="utf-8"))
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    def execute(
        self,
        sql: str,
        params: Iterable[Any] = (),
        *,
        retries: int = 3,
    ) -> sqlite3.Cursor:
        last_error: sqlite3.Error | None = None
        for attempt in range(retries):
            connection: sqlite3.Connection | None = None
            try:
                connection = self.connect()
                cursor = connection.execute(sql, tuple(params))
                connection.commit()
                return cursor
            except sqlite3.Error as exc:
                last_error = exc
                time.sleep(0.1 * (2**attempt))
            finally:
                if connection is not None:
                    connection.close()
        raise RuntimeError(f"Database execute failed: {last_error}") from last_error

    def fetch_one(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Row | None:
        with self.connect() as connection:
            return cast(sqlite3.Row | None, connection.execute(sql, tuple(params)).fetchone())

    def fetch_all(self, sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return list(connection.execute(sql, tuple(params)).fetchall())

    @staticmethod
    def dumps(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, default=str)

    @staticmethod
    def loads(value: str | None, default: Any) -> Any:
        if not value:
            return default
        return json.loads(value)
