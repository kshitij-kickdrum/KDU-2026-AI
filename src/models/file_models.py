from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID


VALID_FILE_TYPES = {"pdf", "image", "audio"}
VALID_STATUSES = {"pending", "processing", "completed", "failed"}
VALID_OPERATIONS = {"vision", "llm", "embedding"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_uuid(value: str) -> None:
    UUID(value)


@dataclass
class FileRecord:
    file_id: str
    display_id: str
    filename: str
    file_type: str
    file_path: str
    file_size_bytes: int
    upload_timestamp: str
    processing_status: str = "pending"
    transcript_path: str | None = None
    summary: str | None = None
    key_points: str | None = None
    topic_tags: str | None = None
    error_message: str | None = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def validate(self) -> None:
        validate_uuid(self.file_id)
        if self.file_type not in VALID_FILE_TYPES:
            raise ValueError(f"Invalid file_type: {self.file_type}")
        if self.processing_status not in VALID_STATUSES:
            raise ValueError(f"Invalid processing_status: {self.processing_status}")


@dataclass
class EmbeddingRecord:
    embedding_id: str
    file_id: str
    chunk_index: int
    chunk_text: str
    chunk_start_char: int
    chunk_end_char: int
    faiss_index_id: int
    created_at: str = field(default_factory=utc_now_iso)

    def validate(self) -> None:
        validate_uuid(self.embedding_id)
        validate_uuid(self.file_id)
        if self.chunk_index < 0:
            raise ValueError("chunk_index must be >= 0")


@dataclass
class CostRecord:
    cost_id: str
    file_id: str | None
    operation_type: str
    model_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    timestamp: str
    metadata: str | None = None

    def validate(self) -> None:
        validate_uuid(self.cost_id)
        if self.file_id:
            validate_uuid(self.file_id)
        if self.operation_type not in VALID_OPERATIONS:
            raise ValueError(f"Invalid operation_type: {self.operation_type}")


@dataclass
class FileUploadResponse:
    file_id: str
    display_id: str
    filename: str
    file_type: str
    status: str
    message: str


@dataclass
class FileStatusResponse:
    file_id: str
    filename: str
    processing_status: str
    progress_percentage: int
    error_message: str | None


@dataclass
class TokenUsage:
    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class VisionExtractionResponse:
    text: str
    page_count: int
    confidence_score: float
    tokens_used: TokenUsage
    cost_usd: float


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass
class TranscriptionResponse:
    text: str
    language: str
    duration_seconds: float
    segments: list[TranscriptSegment]
    confidence_score: float


@dataclass
class SummaryResponse:
    summary: str
    key_points: list[str]
    topic_tags: list[str]
    tokens_used: TokenUsage
    cost_usd: float


@dataclass
class TextChunk:
    chunk_index: int
    text: str
    start_char: int
    end_char: int


@dataclass
class EmbeddingResponse:
    chunks: list[TextChunk]
    embeddings: list[list[float]]
    tokens_used: int
    cost_usd: float


@dataclass
class CostLogResponse:
    cost_id: str
    cost_usd: float
    total_tokens: int


@dataclass
class CostSummary:
    total_cost_usd: float
    total_tokens: int
    by_operation: dict[str, float]
    rows: list[dict[str, Any]]
