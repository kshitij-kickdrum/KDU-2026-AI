from __future__ import annotations

from src.utils.text_processing import chunk_text


def test_chunk_text_basic() -> None:
    text = "Sentence one. Sentence two. Sentence three. " * 40
    chunks = chunk_text(text, chunk_tokens=40, overlap_tokens=5)
    assert len(chunks) >= 2
    assert chunks[0].chunk_index == 0
    assert all(c.text for c in chunks)


def test_chunk_text_empty() -> None:
    assert chunk_text("   ") == []
