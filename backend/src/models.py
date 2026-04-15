from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChunkMetadata(BaseModel):
    section_title: str = ""
    heading_hierarchy: list[str] = Field(default_factory=list)
    chunk_index: int = 0
    overlap_with_previous: int = 0
    overlap_with_next: int = 0
    parent_chunk_id: str | None = None
    document_title: str = ""
    document_source: str = ""

    @field_validator("chunk_index")
    @classmethod
    def chunk_index_non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("chunk_index must be >= 0")
        return value


class ProcessedDocument(BaseModel):
    id: str = Field(default_factory=lambda: f"doc_{uuid4().hex}")
    title: str
    content: str
    source: str
    source_type: Literal["pdf", "url", "text"]
    metadata: dict[str, Any] = Field(default_factory=dict)
    processed_at: datetime = Field(default_factory=utc_now)

    @field_validator("title", "content", "source")
    @classmethod
    def required_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field cannot be empty")
        return value


class Chunk(BaseModel):
    id: str = Field(default_factory=lambda: f"chunk_{uuid4().hex}")
    document_id: str
    content: str
    start_index: int = 0
    end_index: int = 0
    token_count: int = 0
    metadata: ChunkMetadata = Field(default_factory=ChunkMetadata)
    embedding: list[float] | None = None

    @field_validator("content")
    @classmethod
    def non_empty_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("chunk content cannot be empty")
        return value

    @model_validator(mode="after")
    def validate_indices(self) -> "Chunk":
        if self.start_index < 0 or self.end_index < 0:
            raise ValueError("indices must be non-negative")
        if self.end_index < self.start_index:
            raise ValueError("end_index must be >= start_index")
        return self


class RetrievalResult(BaseModel):
    chunk: Chunk
    semantic_score: float = 0.0
    keyword_score: float = 0.0
    combined_score: float = 0.0
    search_method: Literal["semantic", "keyword", "hybrid"] = "hybrid"

    @field_validator("semantic_score", "keyword_score", "combined_score")
    @classmethod
    def score_range(cls, value: float) -> float:
        if value < 0:
            raise ValueError("scores must be >= 0")
        return value


class GeneratedResponse(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    context_used: list[Chunk] = Field(default_factory=list)
    processing_time: float = 0.0
    warnings: list[str] = Field(default_factory=list)

    @field_validator("answer")
    @classmethod
    def answer_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("answer cannot be empty")
        return value

