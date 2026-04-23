from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.models.schemas import CompareRequest, ComparisonResult, ErrorResponse
from app.services.errors import ProviderAPIError

REFERENCE_SENTENCE = "The patient exhibited severe diaphoresis and tachycardia"

router = APIRouter(prefix="/phase1", tags=["phase1"])


@router.post("/compare", response_model=ComparisonResult)
async def compare_embeddings(payload: CompareRequest, request: Request) -> JSONResponse | ComparisonResult:
    embedding_service = request.app.state.embedding_service
    try:
        scores = await embedding_service.embed_all_phase1(payload.query, REFERENCE_SENTENCE)
    except ProviderAPIError as exc:
        error = ErrorResponse(
            error=exc.message,
            provider=exc.provider,
            status_code=exc.status_code,
            detail=exc.detail,
        )
        return JSONResponse(status_code=exc.status_code, content=error.model_dump())

    winner = max(scores, key=lambda item: item.cosine_similarity).model
    return ComparisonResult(
        query=payload.query,
        reference_text=REFERENCE_SENTENCE,
        scores=scores,
        winner=winner,
    )
