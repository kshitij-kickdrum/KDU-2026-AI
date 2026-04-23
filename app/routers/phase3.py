from time import perf_counter

import numpy as np
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.models.schemas import ErrorResponse, QueryRequest, RerankResult, RetrievedChunk
from app.services.errors import ProviderAPIError

router = APIRouter(prefix="/phase3", tags=["phase3"])


@router.post("/rerank", response_model=RerankResult)
async def rerank_query(payload: QueryRequest, request: Request) -> JSONResponse | RerankResult:
    if payload.top_n > payload.top_k:
        error = ErrorResponse(
            error="top_n must be <= top_k",
            provider="internal",
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pagination constraints",
        )
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=error.model_dump())

    embedding_service = request.app.state.embedding_service
    retrieval_service = request.app.state.retrieval_service
    bm25_service = request.app.state.bm25_service
    rerank_service = request.app.state.rerank_service
    child_by_id = request.app.state.child_by_id

    try:
        retrieval_start = perf_counter()
        query_vector = await embedding_service.embed_openai(payload.query, "text-embedding-3-small")
        dense_results = retrieval_service.search_dense(query_vector=query_vector, k=payload.top_k)
        bm25_results = bm25_service.search(query=payload.query, k=payload.top_k)
        rrf_results = retrieval_service.reciprocal_rank_fusion(dense=dense_results, bm25=bm25_results)
        merged_parents = retrieval_service.lookup_parents(rrf_results)
        retrieval_latency_ms = (perf_counter() - retrieval_start) * 1000

        rerank_start = perf_counter()
        reranked_top_n = await rerank_service.rerank(
            query=payload.query,
            parent_docs=merged_parents,
            top_n=payload.top_n,
        )
        rerank_latency_ms = (perf_counter() - rerank_start) * 1000
    except ProviderAPIError as exc:
        error = ErrorResponse(
            error=exc.message,
            provider=exc.provider,
            status_code=exc.status_code,
            detail=exc.detail,
        )
        return JSONResponse(status_code=exc.status_code, content=error.model_dump())
    except Exception as exc:
        error = ErrorResponse(
            error="Retrieval failed",
            provider="faiss",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error.model_dump())

    def to_chunk(item: tuple[int, float]) -> RetrievedChunk:
        child_id, score = item
        child = child_by_id[child_id]
        return RetrievedChunk(
            child_id=child.child_id,
            parent_id=child.parent_id,
            chunk_index=child.chunk_index,
            text=child.text,
            score=float(score),
        )

    dense_top_k = [to_chunk(item) for item in dense_results]
    bm25_top_k = [to_chunk(item) for item in bm25_results]

    return RerankResult(
        query=payload.query,
        dense_top_k=dense_top_k,
        bm25_top_k=bm25_top_k,
        merged_parents=merged_parents,
        reranked_top_n=reranked_top_n,
        retrieval_latency_ms=float(np.round(retrieval_latency_ms, 4)),
        rerank_latency_ms=float(np.round(rerank_latency_ms, 4)),
    )
