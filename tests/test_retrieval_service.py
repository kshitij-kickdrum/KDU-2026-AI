import numpy as np

from app.models.schemas import ChildChunk, ParentDocument
from app.services.retrieval_service import RetrievalService


def _vector(seed: int) -> list[float]:
    rng = np.random.default_rng(seed)
    vec = rng.normal(size=1536).astype(np.float32)
    vec /= np.linalg.norm(vec)
    return vec.tolist()


def _service() -> RetrievalService:
    parents = [
        ParentDocument(parent_id=1, text="Parent one"),
        ParentDocument(parent_id=2, text="Parent two"),
    ]
    chunks = [
        ChildChunk(child_id=1, parent_id=1, chunk_index=0, text="a", vector=_vector(1)),
        ChildChunk(child_id=2, parent_id=1, chunk_index=1, text="b", vector=_vector(2)),
        ChildChunk(child_id=3, parent_id=2, chunk_index=0, text="c", vector=_vector(3)),
    ]
    return RetrievalService(chunks, parents)


def test_rrf_formula_property() -> None:
    dense = [(10, 0.9), (20, 0.8)]
    bm25 = [(20, 8.0), (10, 7.0)]
    merged = RetrievalService.reciprocal_rank_fusion(dense, bm25, k=60)
    scores = dict(merged)
    expected_10 = (1 / (60 + 1)) + (1 / (60 + 2))
    expected_20 = (1 / (60 + 2)) + (1 / (60 + 1))
    assert abs(scores[10] - expected_10) <= 1e-12
    assert abs(scores[20] - expected_20) <= 1e-12


def test_rrf_sorted_descending_property() -> None:
    dense = [(1, 0.9), (2, 0.8), (3, 0.7)]
    bm25 = [(3, 9.0), (1, 8.0), (2, 7.0)]
    merged = RetrievalService.reciprocal_rank_fusion(dense, bm25)
    scores = [score for _, score in merged]
    assert scores == sorted(scores, reverse=True)


def test_lookup_parents_dedup_and_non_empty_chunks() -> None:
    service = _service()
    parents = service.lookup_parents([(1, 0.03), (2, 0.02), (3, 0.01)])
    parent_ids = [p.parent_id for p in parents]
    assert len(parent_ids) == len(set(parent_ids))
    assert all(len(p.matched_chunks) > 0 for p in parents)


def test_rrf_scores_positive_property() -> None:
    dense = [(1, 0.7), (2, 0.6)]
    bm25 = [(2, 3.0), (3, 2.5)]
    merged = RetrievalService.reciprocal_rank_fusion(dense, bm25)
    assert all(score > 0.0 for _, score in merged)
