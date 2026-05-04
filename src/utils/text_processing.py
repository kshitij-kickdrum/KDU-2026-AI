from __future__ import annotations

import re
from typing import Iterable

from src.models.file_models import TextChunk


def _estimate_tokens(text: str) -> int:
    words = len(text.split())
    return max(1, int(words * 1.33))


def chunk_text(text: str, chunk_tokens: int = 500, overlap_tokens: int = 50) -> list[TextChunk]:
    if not text.strip():
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: list[TextChunk] = []

    current_sentences: list[str] = []
    current_tokens = 0
    current_start = 0
    running_index = 0

    def build_chunk(sent_list: Iterable[str], start_char: int, idx: int) -> TextChunk:
        chunk_text_value = " ".join(sent_list).strip()
        end_char = start_char + len(chunk_text_value)
        return TextChunk(chunk_index=idx, text=chunk_text_value, start_char=start_char, end_char=end_char)

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        s_tokens = _estimate_tokens(sentence)

        if current_sentences and current_tokens + s_tokens > chunk_tokens:
            chunk = build_chunk(current_sentences, current_start, running_index)
            chunks.append(chunk)
            running_index += 1

            overlap_text = " ".join(current_sentences)
            overlap_words = overlap_text.split()
            overlap_words = overlap_words[-max(1, overlap_tokens):]
            overlap_chunk = " ".join(overlap_words)

            current_start = max(0, chunk.end_char - len(overlap_chunk))
            current_sentences = [overlap_chunk] if overlap_chunk else []
            current_tokens = _estimate_tokens(overlap_chunk) if overlap_chunk else 0

        if not current_sentences:
            next_pos = text.find(sentence, current_start)
            if next_pos != -1:
                current_start = next_pos

        current_sentences.append(sentence)
        current_tokens += s_tokens

    if current_sentences:
        chunk = build_chunk(current_sentences, current_start, running_index)
        chunks.append(chunk)

    return chunks
