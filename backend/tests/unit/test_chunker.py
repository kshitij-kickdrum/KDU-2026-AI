from src.components.contextual_chunker import ContextualChunker
from src.models import ProcessedDocument


def test_chunker_creates_chunks_with_metadata() -> None:
    doc = ProcessedDocument(
        title="Doc",
        source="unit",
        source_type="text",
        content="# Intro\nThis is sentence one. This is sentence two. " * 80,
    )
    chunker = ContextualChunker(chunk_size=450, overlap_tokens=60, max_chunk_size=250)
    chunks = chunker.chunk_document(doc)
    assert chunks
    assert all(chunk.metadata.document_title == "Doc" for chunk in chunks)

