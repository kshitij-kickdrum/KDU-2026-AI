from collections.abc import AsyncGenerator

import numpy as np
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.models.schemas import ModelScore, ParentContext, RankedDoc
from app.routers.health import router as health_router
from app.routers.phase1 import router as phase1_router
from app.routers.phase3 import router as phase3_router
from app.services.errors import ProviderAPIError


class MockEmbeddingService:
    def __init__(self) -> None:
        self.raise_provider: str | None = None

    async def embed_all_phase1(self, query: str, reference: str) -> list[ModelScore]:
        if self.raise_provider:
            raise ProviderAPIError(
                provider=self.raise_provider,
                status_code=500,
                message="Embedding failed",
                detail="mock failure",
            )
        return [
            ModelScore(
                model="text-embedding-3-small",
                provider="openai",
                cosine_similarity=0.72,
                dimensions=1536,
            ),
            ModelScore(
                model="voyage-4-lite",
                provider="voyageai",
                cosine_similarity=0.91,
                dimensions=1024,
            ),
            ModelScore(
                model="all-MiniLM-L6-v2",
                provider="huggingface",
                cosine_similarity=0.68,
                dimensions=384,
            ),
        ]

    async def embed_openai(self, text: str, model: str = "text-embedding-3-small") -> np.ndarray:
        if self.raise_provider == "openai":
            raise ProviderAPIError(
                provider="openai",
                status_code=500,
                message="Embedding failed",
                detail="mock failure",
            )
        vec = np.ones(1536, dtype=np.float32)
        vec /= np.linalg.norm(vec)
        return vec


class MockBM25Service:
    def search(self, query: str, k: int = 10) -> list[tuple[int, float]]:
        return [(2, 9.5), (1, 7.0), (3, 6.2)][:k]


class MockRetrievalService:
    def search_dense(self, query_vector: np.ndarray, k: int) -> list[tuple[int, float]]:
        return [(1, 0.81), (2, 0.74), (3, 0.69)][:k]

    def reciprocal_rank_fusion(
        self,
        dense: list[tuple[int, float]],
        bm25: list[tuple[int, float]],
        k: int = 60,
    ) -> list[tuple[int, float]]:
        scores: dict[int, float] = {}
        for rank, (child_id, _) in enumerate(dense, start=1):
            scores[child_id] = scores.get(child_id, 0.0) + 1 / (k + rank)
        for rank, (child_id, _) in enumerate(bm25, start=1):
            scores[child_id] = scores.get(child_id, 0.0) + 1 / (k + rank)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    def lookup_parents(self, rrf_results: list[tuple[int, float]]) -> list[ParentContext]:
        return [
            ParentContext(
                parent_id=1,
                text="Parent one context",
                matched_chunks=[1, 2],
                rrf_score=0.0325,
            ),
            ParentContext(
                parent_id=2,
                text="Parent two context",
                matched_chunks=[3],
                rrf_score=0.0161,
            ),
        ]


class MockRerankService:
    def __init__(self) -> None:
        self.raise_provider: str | None = None

    async def rerank(
        self,
        query: str,
        parent_docs: list[ParentContext],
        top_n: int,
    ) -> list[RankedDoc]:
        if self.raise_provider:
            raise ProviderAPIError(
                provider=self.raise_provider,
                status_code=500,
                message="Rerank failed",
                detail="mock failure",
            )
        docs = [
            RankedDoc(doc_id=1, text="Parent one context", relevance_score=0.95, original_dense_rank=1),
            RankedDoc(doc_id=2, text="Parent two context", relevance_score=0.83, original_dense_rank=2),
        ]
        return docs[:top_n]


@pytest.fixture
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(health_router)
    app.include_router(phase1_router)
    app.include_router(phase3_router)

    app.state.embedding_service = MockEmbeddingService()
    app.state.bm25_service = MockBM25Service()
    app.state.retrieval_service = MockRetrievalService()
    app.state.rerank_service = MockRerankService()

    app.state.child_by_id = {
        1: type("Chunk", (), {"child_id": 1, "parent_id": 1, "chunk_index": 0, "text": "A"}),
        2: type("Chunk", (), {"child_id": 2, "parent_id": 1, "chunk_index": 1, "text": "B"}),
        3: type("Chunk", (), {"child_id": 3, "parent_id": 2, "chunk_index": 0, "text": "C"}),
    }
    return app


@pytest_asyncio.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
