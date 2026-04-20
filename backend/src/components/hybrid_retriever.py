from __future__ import annotations

from collections import defaultdict
import re

try:
    from rank_bm25 import BM25Okapi
except Exception:  # noqa: BLE001
    BM25Okapi = None  # type: ignore[assignment]

from src.components.embedding_generator import EmbeddingGenerator
from src.components.vector_database import VectorDatabase
from src.models import RetrievalResult
from src.utils.text import tokenize


class HybridRetriever:
    def __init__(
        self,
        vector_db: VectorDatabase,
        embedding_generator: EmbeddingGenerator,
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.4,
        rrf_k: int = 60,
    ) -> None:
        self.vector_db = vector_db
        self.embedding_generator = embedding_generator
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        self.rrf_k = rrf_k

    def _expand_query(self, query: str) -> str:
        q = query.strip()
        synonyms = {
            "ai": "artificial intelligence",
            "nlp": "natural language processing",
            "llm": "large language model",
            "rag": "retrieval augmented generation",
        }
        parts = [q]
        low = q.lower()
        for k, v in synonyms.items():
            if k in low:
                parts.append(v)
        return " ".join(parts)

    def _extract_phrase_terms(self, query: str) -> list[str]:
        return re.findall(r'"([^"]+)"', query)

    def _extract_boolean_terms(self, query: str) -> tuple[set[str], set[str]]:
        must: set[str] = set()
        must_not: set[str] = set()
        for token in query.split():
            t = token.strip()
            if t.startswith("+") and len(t) > 1:
                must.add(t[1:].lower())
            if t.startswith("-") and len(t) > 1:
                must_not.add(t[1:].lower())
        return must, must_not

    def semantic_search(self, query: str, k: int) -> list[tuple[str, float]]:
        query = self._expand_query(query)
        query_emb = self.embedding_generator._fallback_embedding(query)
        if self.embedding_generator.model:
            try:
                query_emb = self.embedding_generator.model.encode([query], show_progress_bar=False)[0].tolist()
            except Exception:  # noqa: BLE001
                pass
        return self.vector_db.similarity_search(query_emb, k)

    def keyword_search(self, query: str, k: int) -> list[tuple[str, float]]:
        chunks = self.vector_db.list_chunks()
        if not chunks:
            return []
        expanded = self._expand_query(query)
        phrases = self._extract_phrase_terms(query)
        must, must_not = self._extract_boolean_terms(query)

        if BM25Okapi:
            corpus = [tokenize(chunk.content.lower()) for chunk in chunks]
            bm25 = BM25Okapi(corpus)
            scores = bm25.get_scores(tokenize(expanded.lower()))
            ranked = sorted(zip(chunks, scores), key=lambda x: float(x[1]), reverse=True)
            filtered: list[tuple[str, float]] = []
            for chunk, score in ranked:
                text_low = chunk.content.lower()
                terms = set(tokenize(text_low))
                if must and not must.issubset(terms):
                    continue
                if must_not and must_not.intersection(terms):
                    continue
                phrase_bonus = sum(1.0 for p in phrases if p.lower() in text_low)
                final_score = float(score) + phrase_bonus
                if final_score > 0:
                    filtered.append((chunk.id, final_score))
                if len(filtered) >= k:
                    break
            return filtered

        query_terms = set(tokenize(expanded.lower()))
        scored = []
        for chunk in chunks:
            text_low = chunk.content.lower()
            terms = set(tokenize(text_low))
            if must and not must.issubset(terms):
                continue
            if must_not and must_not.intersection(terms):
                continue
            overlap = len(query_terms & terms)
            phrase_bonus = sum(1.0 for p in phrases if p.lower() in text_low)
            if overlap > 0 or phrase_bonus > 0:
                scored.append((chunk.id, float(overlap) + phrase_bonus))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    def fuse_results(self, semantic: list[tuple[str, float]], keyword: list[tuple[str, float]], k: int) -> list[RetrievalResult]:
        chunks_by_id = {chunk.id: chunk for chunk in self.vector_db.list_chunks()}
        sem_rank = {chunk_id: idx + 1 for idx, (chunk_id, _) in enumerate(semantic)}
        key_rank = {chunk_id: idx + 1 for idx, (chunk_id, _) in enumerate(keyword)}
        sem_score = dict(semantic)
        key_score = dict(keyword)

        combined: defaultdict[str, float] = defaultdict(float)
        for chunk_id in set(sem_rank) | set(key_rank):
            if chunk_id in sem_rank:
                combined[chunk_id] += self.semantic_weight * (1.0 / (self.rrf_k + sem_rank[chunk_id]))
            if chunk_id in key_rank:
                combined[chunk_id] += self.keyword_weight * (1.0 / (self.rrf_k + key_rank[chunk_id]))
            # Resolve conflicts in favor of exact-term keyword matches.
            if chunk_id in sem_rank and chunk_id in key_rank and key_score.get(chunk_id, 0.0) > sem_score.get(chunk_id, 0.0):
                combined[chunk_id] += 0.01

        ranked_ids = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:k]
        output: list[RetrievalResult] = []
        for chunk_id, score in ranked_ids:
            chunk = chunks_by_id.get(chunk_id)
            if not chunk:
                continue
            output.append(
                RetrievalResult(
                    chunk=chunk,
                    semantic_score=sem_score.get(chunk_id, 0.0),
                    keyword_score=key_score.get(chunk_id, 0.0),
                    combined_score=score,
                    search_method="hybrid",
                )
            )
        return output

    def retrieve(self, query: str, k: int = 5) -> list[RetrievalResult]:
        semantic: list[tuple[str, float]] = []
        keyword: list[tuple[str, float]] = []
        try:
            semantic = self.semantic_search(query, k=k * 2)
        except Exception:  # noqa: BLE001
            semantic = []
        try:
            keyword = self.keyword_search(query, k=k * 2)
        except Exception:  # noqa: BLE001
            keyword = []
        if not semantic and not keyword:
            return []
        return self.fuse_results(semantic, keyword, k=k)
