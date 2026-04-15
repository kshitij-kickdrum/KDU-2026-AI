from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.models import ChunkMetadata, ProcessedDocument


def test_processed_document_validation() -> None:
    doc = ProcessedDocument(
        title="T",
        content="C",
        source="S",
        source_type="text",
        metadata={"x": 1},
        processed_at=datetime.now(timezone.utc),
    )
    assert doc.title == "T"


def test_processed_document_rejects_empty_content() -> None:
    with pytest.raises(ValidationError):
        ProcessedDocument(title="T", content=" ", source="S", source_type="text")


def test_chunk_metadata_non_negative_index() -> None:
    with pytest.raises(ValidationError):
        ChunkMetadata(chunk_index=-1)

