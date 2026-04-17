from __future__ import annotations

from datetime import UTC, datetime

import aiosqlite
from fastapi import APIRouter, Depends

from app.api.dependencies import Services, get_services

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(services: Services = Depends(get_services)) -> dict:
    db_status = "ok"
    try:
        async with aiosqlite.connect(
            services.config_loader.runtime.settings.app.database_path
        ) as db:
            await db.execute("SELECT 1")
    except Exception:  # noqa: BLE001
        db_status = "error"

    config_status = "ok"
    try:
        _ = services.config_loader.runtime
    except Exception:  # noqa: BLE001
        config_status = "error"

    return {
        "status": "ok" if db_status == "ok" and config_status == "ok" else "degraded",
        "database": db_status,
        "config": config_status,
        "timestamp": datetime.now(UTC).isoformat(),
    }
