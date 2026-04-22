import sqlite3
from contextlib import contextmanager
from pathlib import Path
from queue import Queue
from threading import Lock
from typing import Iterator

from app.config import settings


class SQLiteConnectionPool:
    """Simple SQLite connection pool for local concurrent access."""

    def __init__(self, pool_size: int = 5) -> None:
        self.pool_size = pool_size
        self._queue: Queue[sqlite3.Connection] = Queue(maxsize=pool_size)
        self._lock = Lock()
        self._initialized = False
        self._db_path = self._parse_db_path(settings.database_url)

    @staticmethod
    def _parse_db_path(database_url: str) -> Path:
        if not database_url.startswith("sqlite:///"):
            raise ValueError("Only sqlite:/// URLs are supported")
        rel_path = database_url.removeprefix("sqlite:///")
        return Path(rel_path)

    def initialize(self) -> None:
        with self._lock:
            if self._initialized:
                return
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            for _ in range(self.pool_size):
                conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
                conn.row_factory = sqlite3.Row
                self._queue.put(conn)
            self._initialized = True

    def acquire(self) -> sqlite3.Connection:
        if not self._initialized:
            self.initialize()
        return self._queue.get()

    def release(self, connection: sqlite3.Connection) -> None:
        self._queue.put(connection)

    def close(self) -> None:
        while not self._queue.empty():
            conn = self._queue.get()
            conn.close()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = self.acquire()
        try:
            yield conn
        finally:
            self.release(conn)


pool = SQLiteConnectionPool()
