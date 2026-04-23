import asyncio
import re

import numpy as np
import voyageai
from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer

from app.config import Settings
from app.models.schemas import ModelScore
from app.services.errors import ProviderAPIError
from app.services.similarity_service import cosine_similarity


class EmbeddingService:
    def __init__(self, settings: Settings, hf_model: SentenceTransformer) -> None:
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self._voyage = voyageai.AsyncClient(api_key=settings.voyage_api_key)
        self._voyage_model = settings.voyage_model
        self._hf_model = hf_model

    async def embed_openai(self, text: str, model: str = "text-embedding-3-small") -> np.ndarray:
        try:
            response = await self._openai.embeddings.create(model=model, input=text)
            return np.array(response.data[0].embedding, dtype=np.float32)
        except Exception as exc:
            raise ProviderAPIError(
                provider="openai",
                status_code=self._extract_status_code(exc),
                message="Embedding failed",
                detail=str(exc),
            ) from exc

    async def embed_voyageai(self, text: str, model: str | None = None) -> np.ndarray:
        selected_model = model or self._voyage_model
        try:
            response = await self._voyage.embed(texts=[text], model=selected_model)
            return np.array(response.embeddings[0], dtype=np.float32)
        except Exception as exc:
            raise ProviderAPIError(
                provider="voyageai",
                status_code=self._extract_status_code(exc),
                message="Embedding failed",
                detail=str(exc),
            ) from exc

    def embed_huggingface(self, text: str) -> np.ndarray:
        try:
            embedding = self._hf_model.encode(text, normalize_embeddings=True)
            return np.array(embedding, dtype=np.float32)
        except Exception as exc:
            raise ProviderAPIError(
                provider="huggingface",
                status_code=500,
                message="Embedding failed",
                detail=str(exc),
            ) from exc

    async def embed_all_phase1(self, query: str, reference: str) -> list[ModelScore]:
        async def openai_pair() -> tuple[np.ndarray, np.ndarray]:
            return await asyncio.gather(
                self.embed_openai(query, "text-embedding-3-small"),
                self.embed_openai(reference, "text-embedding-3-small"),
            )

        async def voyage_pair() -> tuple[np.ndarray, np.ndarray]:
            return await asyncio.gather(
                self.embed_voyageai(query, self._voyage_model),
                self.embed_voyageai(reference, self._voyage_model),
            )

        async def hf_pair() -> tuple[np.ndarray, np.ndarray]:
            return await asyncio.to_thread(self._embed_hf_pair, query, reference)

        provider_runs = [
            ("text-embedding-3-small", "openai", openai_pair()),
            (self._voyage_model, "voyageai", voyage_pair()),
            ("all-MiniLM-L6-v2", "huggingface", hf_pair()),
        ]

        raw_results = await asyncio.gather(
            *(run[2] for run in provider_runs),
            return_exceptions=True,
        )

        scores: list[ModelScore] = []
        provider_errors: list[ProviderAPIError] = []
        for (model_name, provider, _), result in zip(provider_runs, raw_results):
            if isinstance(result, Exception):
                if isinstance(result, ProviderAPIError):
                    provider_errors.append(result)
                else:
                    provider_errors.append(
                        ProviderAPIError(
                            provider=provider,
                            status_code=self._extract_status_code(result),
                            message="Embedding failed",
                            detail=str(result),
                        )
                    )
                continue
            scores.append(self._to_model_score(model_name, provider, result[0], result[1]))

        if not scores:
            raise provider_errors[0]
        return scores

    def _embed_hf_pair(self, query: str, reference: str) -> tuple[np.ndarray, np.ndarray]:
        return self.embed_huggingface(query), self.embed_huggingface(reference)

    @staticmethod
    def _extract_status_code(exc: Exception) -> int:
        candidates = [getattr(exc, "status_code", None), getattr(exc, "http_status", None)]
        for code in candidates:
            if isinstance(code, int) and 100 <= code <= 599:
                return code
        text = str(exc)
        match = re.search(r"\b([45]\d{2})\b", text)
        if match:
            return int(match.group(1))
        return 500

    @staticmethod
    def _to_model_score(
        model_name: str,
        provider: str,
        query_vector: np.ndarray,
        reference_vector: np.ndarray,
    ) -> ModelScore:
        score = cosine_similarity(query_vector, reference_vector)
        return ModelScore(
            model=model_name,
            provider=provider,
            cosine_similarity=score,
            dimensions=query_vector.shape[0],
        )
