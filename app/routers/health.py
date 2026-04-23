from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> JSONResponse:
    settings = get_settings()
    missing = []
    if not settings.openai_api_key:
        missing.append("OPENAI_API_KEY")
    if not settings.voyage_api_key:
        missing.append("VOYAGE_API_KEY")
    if not settings.cohere_api_key:
        missing.append("COHERE_API_KEY")

    if missing:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "missing_keys": missing},
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "ok",
            "providers": {
                "openai": "configured",
                "voyageai": "configured",
                "cohere": "configured",
                "huggingface": "local",
            },
        },
    )
