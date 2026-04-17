from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.dependencies import Services, get_services

router = APIRouter(prefix="/admin", tags=["admin"])


class ActivatePromptRequest(BaseModel):
    category: str
    version: str


@router.get("/stats")
async def get_stats(services: Services = Depends(get_services)) -> dict:
    day = datetime.now(UTC).strftime("%Y-%m-%d")
    month = datetime.now(UTC).strftime("%Y-%m")
    daily_stats = await services.cost_tracker.aggregate(day)
    monthly_stats = await services.cost_tracker.aggregate(month)
    return {
        "daily_stats": daily_stats,
        "monthly_stats": monthly_stats,
        "cache_stats": {
            "hit_rate": services.cache.stats.hit_rate,
            "total_entries": await services.cache.total_entries(),
        },
    }


@router.post("/config/reload")
async def reload_config(services: Services = Depends(get_services)) -> dict:
    try:
        services.config_loader.reload()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Reload failed: {exc}") from exc
    return {
        "message": "Configuration reloaded successfully",
        "reloaded_files": [
            "config/settings.yaml",
            "config/models.yaml",
            "config/routing.yaml",
            "config/budget.yaml",
            "prompts/registry.yaml",
        ],
    }


@router.get("/prompts")
async def get_prompts(services: Services = Depends(get_services)) -> dict:
    registry = services.config_loader.runtime.prompt_registry.registry
    output = {
        key: {
            "active_version": value.active_version,
            "available_versions": value.available_versions,
        }
        for key, value in registry.items()
        if key in {"faq", "complaint", "booking"}
    }
    return {"registry": output}


@router.post("/prompts/activate")
async def activate_prompt(
    payload: ActivatePromptRequest, services: Services = Depends(get_services)
) -> dict:
    try:
        previous, new = services.prompt_manager.activate_version(
            payload.category, payload.version
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "message": "Prompt version activated successfully",
        "category": payload.category,
        "previous_version": previous,
        "new_version": new,
    }
