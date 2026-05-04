from __future__ import annotations

from openai import OpenAI

from src.models.file_models import EmbeddingResponse, TextChunk
from src.services.openai_utils import call_openai_with_retry
from src.utils.text_processing import chunk_text


class EmbeddingGenerator:
    def __init__(
        self,
        client: OpenAI,
        model: str = "text-embedding-3-small",
        batch_size: int = 100,
        max_retries: int = 3,
        base_delay: int = 2,
    ) -> None:
        self.client = client
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.base_delay = base_delay

    def create_embeddings(self, text: str) -> EmbeddingResponse:
        chunks = chunk_text(text)
        if not chunks:
            return EmbeddingResponse(chunks=[], embeddings=[], tokens_used=0, cost_usd=0.0)

        embeddings: list[list[float]] = []
        total_tokens = 0

        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i : i + self.batch_size]
            inputs = [chunk.text for chunk in batch]

            def _call() -> object:
                return self.client.embeddings.create(model=self.model, input=inputs)

            response = call_openai_with_retry(
                _call, max_retries=self.max_retries, base_delay=self.base_delay
            )
            for item in response.data:
                embeddings.append(item.embedding)
            usage = getattr(response, "usage", None)
            total_tokens += int(getattr(usage, "total_tokens", 0) or 0)

        return EmbeddingResponse(
            chunks=chunks,
            embeddings=embeddings,
            tokens_used=total_tokens,
            cost_usd=0.0,
        )

    def create_query_embedding(self, query: str) -> tuple[list[float], int]:
        query_text = query.strip()
        if not query_text:
            raise ValueError("Query cannot be empty")

        def _call() -> object:
            return self.client.embeddings.create(model=self.model, input=[query_text])

        response = call_openai_with_retry(_call, max_retries=self.max_retries, base_delay=self.base_delay)
        usage = getattr(response, "usage", None)
        tokens = int(getattr(usage, "total_tokens", 0) or 0)
        return response.data[0].embedding, tokens
