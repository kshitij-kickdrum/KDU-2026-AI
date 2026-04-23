from app.models.schemas import ChildChunk
from app.services.bm25_service import BM25Service


def _chunk(child_id: int, text: str) -> ChildChunk:
    return ChildChunk(
        child_id=child_id,
        parent_id=1,
        chunk_index=child_id - 1,
        text=text,
        vector=[0.0] * 1536,
    )


def test_bm25_exact_keyword_match_is_ranked_high() -> None:
    chunks = [
        _chunk(1, "aspirin therapy and heart prevention"),
        _chunk(2, "kidney monitoring protocol"),
        _chunk(3, "asthma inhaler rescue plan"),
    ]
    service = BM25Service(chunks)
    results = service.search("aspirin heart", k=2)
    assert results[0][0] == 1


def test_bm25_k_limits_results() -> None:
    chunks = [_chunk(i, f"doc {i} common tokens") for i in range(1, 6)]
    service = BM25Service(chunks)
    results = service.search("common", k=3)
    assert len(results) == 3


def test_bm25_empty_query_returns_empty() -> None:
    chunks = [_chunk(1, "some text")]
    service = BM25Service(chunks)
    assert service.search("", k=5) == []
