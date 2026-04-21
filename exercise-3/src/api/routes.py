from __future__ import annotations

import time
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request

from src.api.schemas import (
    ErrorResponse,
    HealthResponse,
    QuestionRequest,
    QuestionResponse,
    RefinementRequest,
    RefinementResponse,
    SummarizationRequest,
    SummarizationResponse,
)

router = APIRouter(prefix="/api/v1", tags=["tri-model-ai-assistant"])


def get_container(request: Request):
    return request.app.state.container


@router.post("/summarize", response_model=SummarizationResponse, responses={400: {"model": ErrorResponse}})
def summarize(payload: SummarizationRequest, container=Depends(get_container)) -> SummarizationResponse:
    start = time.perf_counter()
    result = container.summarization_service.generate_base_summary(payload.text)
    session_id = uuid4()

    container.session_store.create_or_update(
        session_id,
        {
            "base_summary": result["base_summary"],
            "input_word_count": result["input_word_count"],
            "refined_summary": None,
        },
    )

    return SummarizationResponse(
        base_summary=result["base_summary"],
        word_count=result["word_count"],
        input_word_count=result["input_word_count"],
        chunk_count=result["chunk_count"],
        processing_time=time.perf_counter() - start,
        session_id=session_id,
    )


@router.post("/refine", response_model=RefinementResponse, responses={404: {"model": ErrorResponse}})
def refine(payload: RefinementRequest, container=Depends(get_container)) -> RefinementResponse:
    session = container.session_store.get(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail={"error": "Session not found", "code": "SESSION_NOT_FOUND"})

    start = time.perf_counter()
    result = container.summarization_service.refine_summary(
        base_summary=payload.base_summary,
        length_type=payload.length,
        input_word_count=payload.input_word_count,
    )

    container.session_store.create_or_update(payload.session_id, {"refined_summary": result["refined_summary"]})

    return RefinementResponse(
        refined_summary=result["refined_summary"],
        word_count=result["word_count"],
        target_range=result["target_range"],
        compression_ratio=result["compression_ratio"],
        processing_time=time.perf_counter() - start,
        session_id=payload.session_id,
    )


@router.post("/qa", response_model=QuestionResponse, responses={404: {"model": ErrorResponse}})
def qa(payload: QuestionRequest, container=Depends(get_container)) -> QuestionResponse:
    session = container.session_store.get(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail={"error": "Session not found", "code": "SESSION_NOT_FOUND"})

    base_summary = payload.base_summary or session.get("base_summary")
    refined_summary = payload.refined_summary or session.get("refined_summary")

    if not base_summary:
        raise HTTPException(status_code=400, detail={"error": "Base summary is required", "code": "INVALID_INPUT"})

    start = time.perf_counter()
    result = container.qa_service.answer_question(
        question=payload.question,
        base_summary=base_summary,
        refined_summary=refined_summary,
    )

    return QuestionResponse(
        answer=result["answer"],
        confidence=result["confidence"],
        model_used=result["model_used"],
        fallback_level=result["fallback_level"],
        processing_time=time.perf_counter() - start,
        error=result["error"],
        suggestion=result["suggestion"],
        attempts=result["attempts"],
    )


@router.get("/health", response_model=HealthResponse)
def health(container=Depends(get_container)) -> HealthResponse:
    bart_status = "loaded" if container.bart_model.model is not None else "not_loaded"
    roberta_status = "loaded" if container.roberta_model.qa_pipeline is not None else "not_loaded"
    qwen_status = "connected" if container.qwen_client.health_check() else "disconnected"

    return HealthResponse(
        status="healthy" if qwen_status == "connected" else "degraded",
        models={"bart": bart_status, "qwen": qwen_status, "roberta": roberta_status},
        uptime=time.time() - container.startup_time,
    )
