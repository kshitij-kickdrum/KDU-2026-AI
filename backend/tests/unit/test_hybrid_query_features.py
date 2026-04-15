from pathlib import Path
from uuid import uuid4

from src.components.embedding_generator import EmbeddingGenerator
from src.components.hybrid_retriever import HybridRetriever
from src.components.vector_database import VectorDatabase
from src.models import Chunk, ChunkMetadata


def test_phrase_boolean_query_support() -> None:
    db_path = Path("data") / f"test_q_{uuid4().hex}.db"
    db = VectorDatabase(str(db_path))
    emb = EmbeddingGenerator()
    chunks = [
        Chunk(
            document_id="d1",
            content="attention mechanism in transformers model",
            token_count=5,
            end_index=10,
            metadata=ChunkMetadata(document_title="D1", document_source="s1"),
        ),
        Chunk(
            document_id="d2",
            content="convolution neural network basics",
            token_count=4,
            end_index=10,
            metadata=ChunkMetadata(document_title="D2", document_source="s2"),
        ),
    ]
    db.store_chunks(emb.generate_embeddings(chunks))
    retriever = HybridRetriever(db, emb)
    results = retriever.keyword_search('"attention mechanism" +transformers -convolution', k=5)
    assert results
