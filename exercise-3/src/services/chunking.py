from __future__ import annotations

import re
from dataclasses import dataclass

from src.utils.token_counter import TokenCounter

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    chunk_id: int
    text: str
    start_pos: int
    end_pos: int
    token_count: int


class ChunkingService:
    def __init__(self, token_counter: TokenCounter, max_tokens: int = 800, overlap: int = 60) -> None:
        self.token_counter = token_counter
        self.max_tokens = max_tokens
        self.overlap = overlap

    def _split_sentences(self, paragraph: str) -> list[str]:
        return [s.strip() for s in SENTENCE_SPLIT_RE.split(paragraph.strip()) if s.strip()]

    def _split_words_to_fit(self, sentence: str) -> list[str]:
        words = sentence.split()
        pieces: list[str] = []
        current: list[str] = []
        for word in words:
            candidate = " ".join(current + [word])
            if self.token_counter.count_tokens(candidate) <= self.max_tokens:
                current.append(word)
            else:
                if current:
                    pieces.append(" ".join(current))
                current = [word]
        if current:
            pieces.append(" ".join(current))
        return pieces

    def _split_paragraph_to_units(self, paragraph: str) -> list[str]:
        if self.token_counter.count_tokens(paragraph) <= self.max_tokens:
            return [paragraph.strip()]

        units: list[str] = []
        for sentence in self._split_sentences(paragraph):
            if self.token_counter.count_tokens(sentence) <= self.max_tokens:
                units.append(sentence)
            else:
                units.extend(self._split_words_to_fit(sentence))
        return units

    def _last_tokens(self, text: str, count: int) -> str:
        words = text.split()
        if len(words) <= count:
            return text
        return " ".join(words[-count:])

    def chunk_text(self, text: str) -> list[Chunk]:
        clean_text = text.strip()
        if not clean_text:
            return []

        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", clean_text) if p.strip()]
        units: list[str] = []
        for paragraph in paragraphs:
            units.extend(self._split_paragraph_to_units(paragraph))

        chunks: list[Chunk] = []
        current = ""
        search_from = 0

        for unit in units:
            candidate = f"{current}\n\n{unit}".strip() if current else unit
            if self.token_counter.count_tokens(candidate) <= self.max_tokens:
                current = candidate
                continue

            if current:
                start = clean_text.find(current[: min(25, len(current))], search_from)
                start = max(start, 0)
                end = start + len(current)
                chunks.append(
                    Chunk(
                        chunk_id=len(chunks),
                        text=current,
                        start_pos=start,
                        end_pos=end,
                        token_count=self.token_counter.count_tokens(current),
                    )
                )
                search_from = end
                overlap_text = self._last_tokens(current, self.overlap)
                current = f"{overlap_text}\n\n{unit}".strip()
            else:
                current = unit

        if current:
            start = clean_text.find(current[: min(25, len(current))], search_from)
            start = max(start, 0)
            end = start + len(current)
            chunks.append(
                Chunk(
                    chunk_id=len(chunks),
                    text=current,
                    start_pos=start,
                    end_pos=end,
                    token_count=self.token_counter.count_tokens(current),
                )
            )

        return chunks
