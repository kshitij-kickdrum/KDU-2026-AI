from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SearchResult:
    chunk_text: str
    file_id: str
    filename: str
    file_type: str
    similarity_score: float
    context_before: str
    context_after: str
    chunk_index: int


@dataclass
class SearchResponse:
    results: list[SearchResult]
    query_tokens_used: int
    query_cost_usd: float
