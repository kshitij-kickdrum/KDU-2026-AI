from pathlib import Path
from uuid import uuid4

from src.components.embedding_generator import EmbeddingGenerator
from src.components.hybrid_retriever import HybridRetriever
from src.components.vector_database import VectorDatabase
from src.models import Chunk, ChunkMetadata


def test_hybrid_retriever_returns_ranked_results() -> None:
    db_path = Path("data") / f"test_{uuid4().hex}.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = VectorDatabase(db_path=str(db_path))
    emb = EmbeddingGenerator()
    chunks = [
        Chunk(
            document_id="d1",
            content="python is a programming language",
            token_count=6,
            end_index=10,
            metadata=ChunkMetadata(document_title="d1", document_source="s1"),
        ),
        Chunk(
            document_id="d2",
            content="faiss is used for vector search",
            token_count=7,
            end_index=10,
            metadata=ChunkMetadata(document_title="d2", document_source="s2"),
        ),
    ]
    chunks = emb.generate_embeddings(chunks)
    db.store_chunks(chunks)
    retriever = HybridRetriever(db, emb)
    results = retriever.retrieve("python search", k=2)
    assert results
    assert results[0].combined_score >= results[-1].combined_score
