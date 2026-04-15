import pytest

hypothesis = pytest.importorskip("hypothesis")
given = hypothesis.given
settings = hypothesis.settings
st = hypothesis.strategies

from src.components.contextual_chunker import ContextualChunker
from src.models import ProcessedDocument


@settings(max_examples=100)
@given(st.text(min_size=1500, max_size=5000))
def test_property_chunk_token_invariants(text: str) -> None:
    doc = ProcessedDocument(title="Doc", content=text, source="src", source_type="text")
    chunker = ContextualChunker(min_chunk_size=50, max_chunk_size=600, overlap_tokens=60)
    chunks = chunker.chunk_document(doc)
    assert chunks
    for chunk in chunks:
        assert chunk.token_count <= 600
        assert chunk.token_count > 0
