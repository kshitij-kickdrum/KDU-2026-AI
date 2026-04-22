import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(autouse=True)
def _clean_db():
    from app.database.migrations import initialize_database
    from app.database.connection import pool

    initialize_database()
    conn = pool.acquire()
    try:
        conn.execute("DELETE FROM usage_logs")
        conn.execute("DELETE FROM tool_usage")
        conn.execute("DELETE FROM sessions")
        conn.commit()
    finally:
        pool.release(conn)
    yield

