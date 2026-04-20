from pathlib import Path

import pytest

hypothesis = pytest.importorskip("hypothesis")
given = hypothesis.given
settings = hypothesis.settings
st = hypothesis.strategies

from src.components.embedding_generator import EmbeddingGenerator
from src.components.hybrid_retriever import HybridRetriever
from src.components.vector_database import VectorDatabase
from src.models import Chunk, ChunkMetadata


@settings(max_examples=100)
@given(st.lists(st.text(min_size=20, max_size=100), min_size=3, max_size=8))
def test_property_hybrid_fusion_no_duplicates(texts: list[str]) -> None:
    db_file = Path("data") / "tmp_test_meta.db"
    if db_file.exists():
        db_file.unlink()
    db = VectorDatabase(db_path=str(db_file))
    emb = EmbeddingGenerator()
    chunks = [
        Chunk(
            document_id=f"d{i}",
            content=t,
            token_count=max(1, len(t.split())),
            start_index=0,
            end_index=len(t),
            metadata=ChunkMetadata(document_title=f"d{i}", document_source=f"s{i}"),
        )
        for i, t in enumerate(texts)
    ]
    db.store_chunks(emb.generate_embeddings(chunks))
    retriever = HybridRetriever(db, emb)
    results = retriever.retrieve(query="test query", k=5)
    ids = [r.chunk.id for r in results]
    assert len(ids) == len(set(ids))
