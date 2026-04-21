from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SummarizationRequest(BaseModel):
    text: str = Field(min_length=100)


class SummarizationResponse(BaseModel):
    base_summary: str
    word_count: int
    input_word_count: int
    chunk_count: int
    processing_time: float
    session_id: UUID


class RefinementRequest(BaseModel):
    base_summary: str = Field(min_length=50)
    length: Literal["short", "medium", "long"]
    input_word_count: int = Field(gt=0)
    session_id: UUID


class RefinementResponse(BaseModel):
    refined_summary: str
    word_count: int
    target_range: dict[str, int]
    compression_ratio: float
    processing_time: float
    session_id: UUID


class QuestionRequest(BaseModel):
    question: str = Field(min_length=5)
    refined_summary: str | None = None
    base_summary: str | None = None
    session_id: UUID


class QAAttempt(BaseModel):
    level: int = Field(ge=1, le=4)
    model: str
    context_type: Literal["refined", "base", "compressed"]
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    result: Literal["success", "low_confidence", "not_found"]


class QuestionResponse(BaseModel):
    answer: str | None
    confidence: float = Field(ge=0.0, le=1.0)
    model_used: Literal["roberta", "qwen_fallback"]
    fallback_level: int = Field(ge=1, le=4)
    processing_time: float
    error: str | None = None
    suggestion: str | None = None
    attempts: list[QAAttempt] | None = None


class HealthResponse(BaseModel):
    status: str
    models: dict[str, str]
    uptime: float


class ErrorResponse(BaseModel):
    error: str
    code: str

    @field_validator("error", "code")
    @classmethod
    def non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value
