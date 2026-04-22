from datetime import datetime, timezone

from fastapi import APIRouter

from app.api.chat import llm_service
from app.database.connection import pool


router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    database_status = "connected"
    try:
        conn = pool.acquire()
        conn.execute("SELECT 1")
    except Exception:
        database_status = "disconnected"
    finally:
        try:
            pool.release(conn)
        except Exception:
            pass

    return {
        "status": "healthy" if database_status == "connected" else "degraded",
        "services": {
            "database": database_status,
            "llm_provider": llm_service.get_current_provider(),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

