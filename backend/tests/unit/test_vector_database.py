from pathlib import Path
from uuid import uuid4

from src.components.vector_database import VectorDatabase
from src.models import Chunk, ChunkMetadata


def test_list_and_delete_documents() -> None:
    db_path = Path("data") / f"test_docs_{uuid4().hex}.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = VectorDatabase(db_path=str(db_path))

    chunks = [
        Chunk(
            document_id="doc_a",
            content="alpha text",
            token_count=2,
            start_index=0,
            end_index=10,
            metadata=ChunkMetadata(document_title="Doc A", document_source="source-a"),
            embedding=[0.1, 0.2, 0.3],
        ),
        Chunk(
            document_id="doc_a",
            content="alpha more text",
            token_count=3,
            start_index=0,
            end_index=15,
            metadata=ChunkMetadata(document_title="Doc A", document_source="source-a"),
            embedding=[0.1, 0.2, 0.3],
        ),
        Chunk(
            document_id="doc_b",
            content="beta text",
            token_count=2,
            start_index=0,
            end_index=9,
            metadata=ChunkMetadata(document_title="Doc B", document_source="source-b"),
            embedding=[0.3, 0.2, 0.1],
        ),
    ]
    db.store_chunks(chunks)
    docs = db.list_documents()
    ids = {doc["document_id"] for doc in docs}
    assert "doc_a" in ids
    assert "doc_b" in ids
    removed = db.delete_document("doc_a")
    assert removed >= 1
