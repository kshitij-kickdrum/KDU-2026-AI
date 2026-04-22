from app.database.connection import pool
from app.database.models import SESSIONS_TABLE, TOOL_USAGE_TABLE, USAGE_LOGS_TABLE


def initialize_database() -> None:
    pool.initialize()
    conn = pool.acquire()
    try:
        cursor = conn.cursor()
        cursor.execute(SESSIONS_TABLE)
        cursor.execute(USAGE_LOGS_TABLE)
        cursor.execute(TOOL_USAGE_TABLE)
        conn.commit()
    finally:
        pool.release(conn)

