from src.components.reranker import Reranker
from src.models import Chunk, ChunkMetadata, RetrievalResult


def _result(doc_id: str, content: str, base: float) -> RetrievalResult:
    chunk = Chunk(
        document_id=doc_id,
        content=content,
        token_count=max(1, len(content.split())),
        start_index=0,
        end_index=len(content),
        metadata=ChunkMetadata(document_title=doc_id, document_source=f"{doc_id}.txt"),
    )
    return RetrievalResult(chunk=chunk, combined_score=base, semantic_score=base, keyword_score=base)


def test_rerank_and_threshold() -> None:
    rr = Reranker(min_relevance_threshold=0.3)
    items = [
        _result("d1", "attention mechanism transformers", 0.4),
        _result("d2", "random unrelated text", 0.1),
    ]
    out = rr.rerank_results(items, "what is attention in transformers")
    assert out
    assert out[0].combined_score >= out[-1].combined_score


def test_fit_context_window_diversity() -> None:
    rr = Reranker(min_relevance_threshold=0.0, max_context_tokens=100)
    items = [
        _result("d1", "attention mechanism in transformers model", 0.9),
        _result("d1", "self attention query key value", 0.8),
        _result("d1", "encoder decoder architecture", 0.7),
        _result("d2", "recurrent neural network baseline", 0.6),
    ]
    selected = rr.fit_context_window(items, k=3)
    assert len(selected) == 3
    docs = [s.chunk.document_id for s in selected]
    assert "d2" in docs

