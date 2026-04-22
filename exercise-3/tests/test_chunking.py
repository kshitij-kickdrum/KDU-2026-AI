from src.services.chunking import ChunkingService
from src.utils.token_counter import TokenCounter


def test_chunk_text_splits_large_input():
    counter = TokenCounter(max_tokens=512)
    chunker = ChunkingService(token_counter=counter, max_tokens=30, overlap=5)

    text = (
        "Paragraph one has several words and enough material to force chunking. "
        "It keeps going to make sure token count grows.\n\n"
        "Paragraph two continues with additional text to exceed the threshold and "
        "exercise overlap behavior between chunks."
    )

    chunks = chunker.chunk_text(text)
    assert len(chunks) >= 2
    assert chunks[0].token_count <= 30


def test_chunk_text_handles_empty_input():
    counter = TokenCounter()
    chunker = ChunkingService(token_counter=counter)
    assert chunker.chunk_text("   ") == []


def test_chunk_text_sentence_and_word_fallback():
    counter = TokenCounter(max_tokens=512)
    chunker = ChunkingService(token_counter=counter, max_tokens=8, overlap=2)
    text = "Verylongsentence withmany words to split because it is huge and has no paragraph breaks."

    chunks = chunker.chunk_text(text)
    assert len(chunks) >= 2
    assert all(chunk.token_count <= 8 for chunk in chunks)
