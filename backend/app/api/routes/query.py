from __future__ import annotations

import logging
import time
from collections import deque
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.dependencies import Services, get_services
from app.core.cost_tracker import CostRecord
from app.core.llm_client import LLMServiceUnavailable
from app.models.request import QueryRequest
from app.models.response import BudgetStatusResponse, QueryResponse, TokenUsage

router = APIRouter(tags=["query"])
logger = logging.getLogger(__name__)


def _check_rate_limit(request: Request, limit: int) -> None:
    ip = request.client.host if request.client else "unknown"
    bucket: dict[str, deque[float]] = request.app.state.rate_limits
    now = time.time()
    window_start = now - 60
    q = bucket.setdefault(ip, deque())
    while q and q[0] < window_start:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    q.append(now)


@router.post("/query", response_model=QueryResponse)
async def query_endpoint(
    payload: QueryRequest,
    request: Request,
    services: Services = Depends(get_services),
) -> QueryResponse:
    start = time.perf_counter()
    runtime = services.config_loader.runtime
    _check_rate_limit(request, runtime.settings.limits.rate_limit_requests_per_minute)

    budget_status = await services.budget_guard.check_budget()
    cached = None
    if runtime.settings.features.enable_response_cache:
        cached = await services.cache.get(payload.query)
    query_id = str(uuid4())

    if cached is not None:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return QueryResponse(
            query_id=query_id,
            response=cached,
            category=payload.override_category or "faq",
            complexity=payload.override_complexity or "low",
            model_used="cache",
            prompt_version="n/a",
            classification_method="cache_hit",
            tokens=TokenUsage(prompt=0, completion=0),
            cost_usd=0.0,
            cache_hit=True,
            was_summarized=False,
            budget_status=BudgetStatusResponse(
                daily_remaining_usd=float(budget_status.daily_remaining_usd),
                budget_fallback_active=budget_status.budget_fallback_active,
            ),
            latency_ms=latency_ms,
        )

    try:
        if payload.override_category and payload.override_complexity:
            category = payload.override_category
            complexity = payload.override_complexity
            classification_method = "override"
        else:
            classification = await services.classifier.classify(payload.query)
            category = payload.override_category or classification.category
            complexity = payload.override_complexity or classification.complexity
            classification_method = classification.method

        model_key = services.router.route(
            category=category,
            complexity=complexity,
            budget_fallback_active=budget_status.budget_fallback_active,
        )

        summary_result = await services.summarizer.maybe_summarize(payload.query)
        prompt, prompt_version = services.prompt_manager.render(category, summary_result.text)

        llm_result = await services.llm_client.complete(
            model_key=model_key, prompt=prompt, query=summary_result.text
        )
    except LLMServiceUnavailable as exc:
        logger.exception(
            "LLM service unavailable while handling query",
            extra={"context": {"query_id": query_id, "error": str(exc)}},
        )
        raise HTTPException(
            status_code=503,
            detail=f"LLM service unavailable. {exc}",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unhandled query processing error")
        raise HTTPException(
            status_code=500,
            detail="Query processing failed unexpectedly. Check backend logs.",
        ) from exc
    model = runtime.models.models[model_key]
    cost = services.cost_tracker.calculate_cost(
        llm_result.prompt_tokens, llm_result.completion_tokens, model
    )

    if runtime.settings.features.enable_response_cache:
        await services.cache.set(payload.query, category, llm_result.text)

    if runtime.settings.features.enable_cost_tracking:
        await services.cost_tracker.record(
            CostRecord(
                id=query_id,
                session_id=payload.session_id,
                query_text=payload.query,
                category=category,
                complexity=complexity,
                model_used=model_key,
                prompt_version=prompt_version,
                classification_method=classification_method,
                prompt_tokens=llm_result.prompt_tokens,
                completion_tokens=llm_result.completion_tokens,
                cost_usd=cost,
                budget_fallback_active=budget_status.budget_fallback_active,
                latency_ms=int((time.perf_counter() - start) * 1000),
            )
        )

    latency_ms = int((time.perf_counter() - start) * 1000)
    return QueryResponse(
        query_id=query_id,
        response=llm_result.text,
        category=category,
        complexity=complexity,
        model_used=model_key,
        prompt_version=prompt_version,
        classification_method=classification_method,
        tokens=TokenUsage(
            prompt=llm_result.prompt_tokens,
            completion=llm_result.completion_tokens,
        ),
        cost_usd=float(cost.quantize(Decimal("0.00000001"))),
        cache_hit=False,
        was_summarized=summary_result.was_summarized,
        budget_status=BudgetStatusResponse(
            daily_remaining_usd=float(budget_status.daily_remaining_usd),
            budget_fallback_active=budget_status.budget_fallback_active,
        ),
        latency_ms=latency_ms,
    )
