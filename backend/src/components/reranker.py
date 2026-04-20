from __future__ import annotations

from src.models import RetrievalResult
from src.utils.text import token_count, tokenize


class Reranker:
    def __init__(self, min_relevance_threshold: float = 0.3, max_context_tokens: int = 4000) -> None:
        self.min_relevance_threshold = min_relevance_threshold
        self.max_context_tokens = max_context_tokens

    def calculate_relevance_score(self, result: RetrievalResult, query: str) -> float:
        stop = {"what", "is", "are", "the", "a", "an", "of", "to", "in", "on", "for", "and"}
        query_terms = {t for t in tokenize(query.lower()) if t.isalnum() and t not in stop}
        chunk_terms = set(tokenize(result.chunk.content.lower()))
        coverage = len(query_terms & chunk_terms) / max(1, len(query_terms))
        return (result.combined_score * 0.7) + (coverage * 0.3)

    def rerank_results(self, results: list[RetrievalResult], query: str) -> list[RetrievalResult]:
        scored: list[RetrievalResult] = []
        for item in results:
            item.combined_score = self.calculate_relevance_score(item, query)
            if item.combined_score >= self.min_relevance_threshold:
                scored.append(item)
        scored.sort(key=lambda r: r.combined_score, reverse=True)
        if scored:
            return scored
        # Fallback: if everything is filtered out, keep best candidates instead of empty context.
        relaxed = list(results)
        relaxed.sort(key=lambda r: r.combined_score, reverse=True)
        return relaxed[: max(1, min(5, len(relaxed)))]

    def fit_context_window(self, results: list[RetrievalResult], k: int = 5) -> list[RetrievalResult]:
        selected: list[RetrievalResult] = []
        used_tokens = 0
        per_doc_count: dict[str, int] = {}
        max_per_doc = 2

        # First pass: enforce per-document cap for diversity.
        for result in results:
            chunk_tokens = result.chunk.token_count or token_count(result.chunk.content)
            if len(selected) >= k:
                break
            if used_tokens + chunk_tokens > self.max_context_tokens:
                continue
            doc_id = result.chunk.document_id
            if per_doc_count.get(doc_id, 0) >= max_per_doc:
                continue
            selected.append(result)
            used_tokens += chunk_tokens
            per_doc_count[doc_id] = per_doc_count.get(doc_id, 0) + 1

        # Second pass: if still under k, fill with best remaining regardless of document.
        if len(selected) < k:
            selected_ids = {item.chunk.id for item in selected}
            for result in results:
                if len(selected) >= k:
                    break
                if result.chunk.id in selected_ids:
                    continue
                chunk_tokens = result.chunk.token_count or token_count(result.chunk.content)
                if used_tokens + chunk_tokens > self.max_context_tokens:
                    continue
                selected.append(result)
                used_tokens += chunk_tokens
                selected_ids.add(result.chunk.id)
        return selected
