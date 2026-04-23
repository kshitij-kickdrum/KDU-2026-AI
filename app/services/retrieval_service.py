from collections import defaultdict

import faiss
import numpy as np

from app.models.schemas import ChildChunk, ParentContext, ParentDocument
from app.services.similarity_service import cosine_similarity


class RetrievalService:
    def __init__(self, chunks: list[ChildChunk], parent_store: list[ParentDocument]) -> None:
        self._chunks = chunks
        self._child_by_id = {chunk.child_id: chunk for chunk in chunks}
        self._parent_by_id = {parent.parent_id: parent for parent in parent_store}
        self._child_vectors = np.array([chunk.vector for chunk in chunks], dtype=np.float32)
        self._index = faiss.IndexFlatIP(1536)
        self._index.add(self._child_vectors)

    def search_dense(self, query_vector: np.ndarray, k: int) -> list[tuple[int, float]]:
        if query_vector.shape[0] != 1536:
            raise ValueError("query vector must have dimension 1536")
        query = query_vector.astype(np.float32, copy=False).reshape(1, -1)
        _, indices = self._index.search(query, k)

        results: list[tuple[int, float]] = []
        for idx in indices[0]:
            if idx < 0:
                continue
            child = self._chunks[int(idx)]
            child_vec = np.array(child.vector, dtype=np.float32)
            score = cosine_similarity(query_vector, child_vec)
            results.append((child.child_id, score))
        return results

    @staticmethod
    def reciprocal_rank_fusion(
        dense: list[tuple[int, float]],
        bm25: list[tuple[int, float]],
        k: int = 60,
    ) -> list[tuple[int, float]]:
        scores: dict[int, float] = {}
        for rank, (child_id, _) in enumerate(dense, start=1):
            scores[child_id] = scores.get(child_id, 0.0) + 1.0 / (k + rank)
        for rank, (child_id, _) in enumerate(bm25, start=1):
            scores[child_id] = scores.get(child_id, 0.0) + 1.0 / (k + rank)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    def lookup_parents(self, rrf_results: list[tuple[int, float]]) -> list[ParentContext]:
        grouped: dict[int, dict[str, object]] = defaultdict(
            lambda: {"matched_chunks": [], "rrf_score": 0.0}
        )

        for child_id, rrf_score in rrf_results:
            chunk = self._child_by_id.get(child_id)
            if chunk is None:
                continue
            parent_row = grouped[chunk.parent_id]
            matched_chunks = parent_row["matched_chunks"]
            if isinstance(matched_chunks, list):
                matched_chunks.append(child_id)
            parent_row["rrf_score"] = float(parent_row["rrf_score"]) + rrf_score

        result: list[ParentContext] = []
        for parent_id, info in grouped.items():
            parent_doc = self._parent_by_id.get(parent_id)
            if parent_doc is None:
                continue
            result.append(
                ParentContext(
                    parent_id=parent_id,
                    text=parent_doc.text,
                    matched_chunks=sorted(set(info["matched_chunks"])),
                    rrf_score=float(info["rrf_score"]),
                )
            )
        result.sort(key=lambda item: item.rrf_score, reverse=True)
        return result
