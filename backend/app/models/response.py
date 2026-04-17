from __future__ import annotations

from pydantic import BaseModel


class TokenUsage(BaseModel):
    prompt: int
    completion: int


class BudgetStatusResponse(BaseModel):
    daily_remaining_usd: float
    budget_fallback_active: bool


class QueryResponse(BaseModel):
    query_id: str
    response: str
    category: str
    complexity: str
    model_used: str
    prompt_version: str
    classification_method: str
    tokens: TokenUsage
    cost_usd: float
    cache_hit: bool
    was_summarized: bool
    budget_status: BudgetStatusResponse
    latency_ms: int
