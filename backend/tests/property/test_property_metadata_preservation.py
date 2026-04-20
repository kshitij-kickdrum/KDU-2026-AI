import pytest

hypothesis = pytest.importorskip("hypothesis")
given = hypothesis.given
settings = hypothesis.settings
st = hypothesis.strategies

from src.components.contextual_chunker import ContextualChunker
from src.models import ProcessedDocument


@settings(max_examples=100)
@given(st.text(min_size=1000, max_size=3000))
def test_property_metadata_preservation(text: str) -> None:
    doc = ProcessedDocument(title="Title", content=text, source="src", source_type="text")
    chunker = ContextualChunker()
    chunks = chunker.chunk_document(doc)
    for chunk in chunks:
        assert chunk.metadata.document_title == "Title"
        assert chunk.metadata.document_source == "src"
