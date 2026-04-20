from __future__ import annotations

import re

from src.models import Chunk, ChunkMetadata, ProcessedDocument
from src.utils.text import sentence_split, token_count, tokenize


class ContextualChunker:
    def __init__(
        self,
        chunk_size: int = 450,
        overlap_tokens: int = 60,
        min_chunk_size: int = 100,
        max_chunk_size: int = 600,
        semantic_refinement_threshold: int = 600,
        enable_parent_child: bool = False,
    ) -> None:
        self.chunk_size = chunk_size
        self.overlap_tokens = overlap_tokens
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.semantic_refinement_threshold = semantic_refinement_threshold
        self.enable_parent_child = enable_parent_child

    def structural_split(self, content: str) -> list[tuple[str, str]]:
        # Keep markdown and html heading lines as section boundaries.
        lines = content.splitlines()
        sections: list[tuple[str, list[str]]] = []
        current_heading = "Document"
        buffer: list[str] = []
        in_code_block = False

        heading_pattern = re.compile(r"^(#{1,6}\s+.+|<h[1-6][^>]*>.*?</h[1-6]>)$", re.IGNORECASE)
        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
            # Preserve code/table blocks as atomic by not splitting on headings while inside them.
            if in_code_block:
                buffer.append(line)
                continue
            if heading_pattern.match(line.strip()):
                if buffer:
                    sections.append((current_heading, buffer))
                current_heading = re.sub(r"<[^>]+>", "", line).lstrip("#").strip()
                buffer = []
            else:
                buffer.append(line)
        if buffer:
            sections.append((current_heading, buffer))
        return [(heading, "\n".join(text).strip()) for heading, text in sections if "\n".join(text).strip()]

    def token_aware_split(self, section_text: str) -> list[str]:
        sentences = sentence_split(section_text)
        if not sentences:
            return [section_text]

        chunks: list[str] = []
        current: list[str] = []
        current_tokens = 0
        for sent in sentences:
            sent_tokens = token_count(sent)
            if current and current_tokens + sent_tokens > self.max_chunk_size:
                chunks.append(" ".join(current))
                overlap = self._build_overlap(current)
                current = overlap + [sent]
                current_tokens = token_count(" ".join(current))
            else:
                current.append(sent)
                current_tokens += sent_tokens

        if current:
            chunks.append(" ".join(current))
        return chunks

    def _build_overlap(self, current_sentences: list[str]) -> list[str]:
        if self.overlap_tokens <= 0:
            return []
        out: list[str] = []
        total = 0
        for sent in reversed(current_sentences):
            out.insert(0, sent)
            total += token_count(sent)
            if total >= self.overlap_tokens:
                break
        return out

    def semantic_refinement(self, chunks: list[str]) -> list[str]:
        refined: list[str] = []
        for chunk in chunks:
            tc = token_count(chunk)
            if tc > self.semantic_refinement_threshold:
                # Coherence-aware split: prefer break near paragraph boundary.
                tokens = tokenize(chunk)
                midpoint = len(tokens) // 2
                para_break = chunk.find("\n\n", max(0, len(chunk) // 3))
                if para_break > 0:
                    left_text = chunk[:para_break]
                    right_text = chunk[para_break:]
                    left = left_text.strip()
                    right = right_text.strip()
                else:
                    left = " ".join(tokens[:midpoint]).strip()
                    right = " ".join(tokens[midpoint:]).strip()
                if left:
                    refined.append(left)
                if right:
                    refined.append(right)
            else:
                refined.append(chunk)

        # Merge tiny chunks with previous to preserve coherence.
        merged: list[str] = []
        for chunk in refined:
            if merged and token_count(chunk) < self.min_chunk_size:
                merged[-1] = f"{merged[-1]} {chunk}".strip()
            else:
                merged.append(chunk)
        return merged

    def chunk_document(self, document: ProcessedDocument) -> list[Chunk]:
        sections = self.structural_split(document.content) or [("Document", document.content)]
        output: list[Chunk] = []
        running_index = 0
        for section_title, section_text in sections:
            parent_id: str | None = None
            if self.enable_parent_child:
                parent_id = f"parent_{document.id}_{len(output)}"
            initial_chunks = self.token_aware_split(section_text)
            final_chunks = self.semantic_refinement(initial_chunks)
            for idx, chunk_text in enumerate(final_chunks):
                tokens = token_count(chunk_text)
                metadata = ChunkMetadata(
                    section_title=section_title,
                    heading_hierarchy=[section_title],
                    chunk_index=len(output),
                    overlap_with_previous=self.overlap_tokens if output else 0,
                    overlap_with_next=self.overlap_tokens if idx < len(final_chunks) - 1 else 0,
                    parent_chunk_id=parent_id,
                    document_title=document.title,
                    document_source=document.source,
                )
                output.append(
                    Chunk(
                        document_id=document.id,
                        content=chunk_text,
                        start_index=running_index,
                        end_index=running_index + len(chunk_text),
                        token_count=tokens,
                        metadata=metadata,
                    )
                )
                running_index += len(chunk_text)
        return output
