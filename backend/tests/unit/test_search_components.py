from pathlib import Path
from uuid import uuid4

from src.components.embedding_generator import EmbeddingGenerator
from src.components.hybrid_retriever import HybridRetriever
from src.components.vector_database import VectorDatabase
from src.models import Chunk, ChunkMetadata


def _build_db() -> tuple[VectorDatabase, EmbeddingGenerator]:
    db_path = Path("data") / f"test_search_{uuid4().hex}.db"
    db = VectorDatabase(str(db_path))
    emb = EmbeddingGenerator()
    chunks = [
        Chunk(
            document_id="doc1",
            content="attention mechanism powers transformers architecture",
            token_count=6,
            start_index=0,
            end_index=10,
            metadata=ChunkMetadata(document_title="Doc1", document_source="d1"),
        ),
        Chunk(
            document_id="doc2",
            content="keyword search with bm25 exact match retrieval",
            token_count=7,
            start_index=0,
            end_index=10,
            metadata=ChunkMetadata(document_title="Doc2", document_source="d2"),
        ),
    ]
    db.store_chunks(emb.generate_embeddings(chunks))
    return db, emb


def test_semantic_search_non_empty() -> None:
    db, emb = _build_db()
    retriever = HybridRetriever(db, emb)
    out = retriever.semantic_search("transformers attention", k=2)
    assert out


def test_keyword_phrase_boolean() -> None:
    db, emb = _build_db()
    retriever = HybridRetriever(db, emb)
    out = retriever.keyword_search('"attention mechanism" +transformers -bm25', k=3)
    assert out


def test_retrieve_graceful_degradation() -> None:
    db, emb = _build_db()
    retriever = HybridRetriever(db, emb)

    def boom(*args, **kwargs):  # noqa: ANN001, ANN002
        raise RuntimeError("boom")

    sample_chunk_id = db.list_chunks()[0].id
    retriever.semantic_search = boom  # type: ignore[method-assign]
    retriever.keyword_search = lambda query, k: [(sample_chunk_id, 1.0)]  # type: ignore[method-assign]
    out = retriever.retrieve("anything", k=2)
    assert out
