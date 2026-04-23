from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class EmbeddingRecord(BaseModel):
    text: str = Field(min_length=1, max_length=8192)
    model: Literal[
        "text-embedding-3-small",
        "text-embedding-3-large",
        "voyage-4-large",
        "voyage-4",
        "voyage-4-lite",
        "voyage-law-2",
        "voyage-finance-2",
        "voyage-code-3",
        "all-MiniLM-L6-v2",
    ]
    provider: Literal["openai", "voyageai", "huggingface"]
    vector: list[float] = Field(min_length=1)
    dimensions: int = Field(gt=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ParentDocument(BaseModel):
    parent_id: int = Field(gt=0)
    text: str = Field(min_length=1, max_length=4096)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChildChunk(BaseModel):
    child_id: int = Field(gt=0)
    parent_id: int = Field(gt=0)
    chunk_index: int = Field(ge=0)
    text: str = Field(min_length=1, max_length=512)
    vector: list[float] = Field(min_length=1536, max_length=1536)


class CompareRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2048)


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2048)
    top_k: int = Field(default=10, ge=1, le=50)
    top_n: int = Field(default=5, ge=1, le=50)


class ModelScore(BaseModel):
    model: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    cosine_similarity: float = Field(ge=-1.0, le=1.0)
    dimensions: int = Field(gt=0)


class ComparisonResult(BaseModel):
    query: str = Field(min_length=1)
    reference_text: str = Field(min_length=1)
    scores: list[ModelScore] = Field(min_length=1)
    winner: str = Field(min_length=1)


class MatryoshkaResult(BaseModel):
    original_dims: int = Field(gt=0)
    truncated_dims: int = Field(gt=0)
    cosine_similarity: float = Field(ge=-1.0, le=1.0)
    memory_bytes_original: int = Field(ge=0)
    memory_bytes_compressed: int = Field(ge=0)
    compression_ratio: float = Field(gt=0)


class BinaryResult(BaseModel):
    original_dims: int = Field(gt=0)
    hamming_distance: int = Field(ge=0)
    memory_bytes_original: int = Field(ge=0)
    memory_bytes_compressed: int = Field(ge=0)
    compression_ratio: float = Field(gt=0)


class MatryoshkaThenBinaryResult(BaseModel):
    original_dims: int = Field(gt=0)
    truncated_dims: int = Field(gt=0)
    hamming_distance: int = Field(ge=0)
    memory_bytes_original: int = Field(ge=0)
    memory_bytes_compressed: int = Field(ge=0)
    compression_ratio: float = Field(gt=0)
    normalization_applied: bool = True


class CompressionComparisonResult(BaseModel):
    text_a: str = Field(min_length=1)
    text_b: str = Field(min_length=1)
    matryoshka: MatryoshkaResult
    binary: BinaryResult
    matryoshka_then_binary: MatryoshkaThenBinaryResult


class RetrievedChunk(BaseModel):
    child_id: int = Field(gt=0)
    parent_id: int = Field(gt=0)
    chunk_index: int = Field(ge=0)
    text: str = Field(min_length=1)
    score: float


class ParentContext(BaseModel):
    parent_id: int = Field(gt=0)
    text: str = Field(min_length=1)
    matched_chunks: list[int] = Field(min_length=1)
    rrf_score: float = Field(gt=0.0)


class RankedDoc(BaseModel):
    doc_id: int = Field(gt=0)
    text: str = Field(min_length=1)
    relevance_score: float = Field(ge=0.0, le=1.0)
    original_dense_rank: int = Field(gt=0)


class RerankResult(BaseModel):
    query: str = Field(min_length=1)
    dense_top_k: list[RetrievedChunk]
    bm25_top_k: list[RetrievedChunk]
    merged_parents: list[ParentContext]
    reranked_top_n: list[RankedDoc]
    retrieval_latency_ms: float = Field(ge=0.0)
    rerank_latency_ms: float = Field(ge=0.0)


class ErrorResponse(BaseModel):
    error: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    status_code: int = Field(ge=100, le=599)
    detail: str = Field(default="")
