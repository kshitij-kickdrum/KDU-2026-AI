from __future__ import annotations

import hashlib
import logging
import math
from typing import Iterable

try:
    import numpy as np
except Exception:  # noqa: BLE001
    np = None  # type: ignore[assignment]

from src.models import Chunk
from src.utils.cache import CacheManager
from src.utils.text import token_count

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # noqa: BLE001
    SentenceTransformer = None  # type: ignore[assignment]


class EmbeddingGenerator:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", batch_size: int = 32, max_input_tokens: int = 800) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_input_tokens = max_input_tokens
        self.cache = CacheManager()
        self.model = None
        if SentenceTransformer:
            try:
                self.model = SentenceTransformer(model_name)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Could not load embedding model '%s'. Falling back to hash embeddings. Error: %s",
                    model_name,
                    exc,
                )

    def _fallback_embedding(self, text: str, dim: int = 384) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        data = list((digest * ((dim // len(digest)) + 1))[:dim])
        mean = sum(data) / len(data)
        var = sum((x - mean) ** 2 for x in data) / max(1, len(data))
        std = math.sqrt(var) + 1e-6
        return [float((x - mean) / std) for x in data]

    def generate_embeddings(self, chunks: list[Chunk]) -> list[Chunk]:
        non_empty = [chunk for chunk in chunks if chunk.content.strip()]
        if not non_empty:
            return []

        texts = []
        keys = []
        for c in non_empty:
            key = hashlib.sha256(c.content.encode("utf-8")).hexdigest()
            keys.append(key)
            cached = self.cache.get_embedding(key)
            if cached:
                c.embedding = cached
                texts.append("")
            else:
                if token_count(c.content) > self.max_input_tokens:
                    logger.info("Truncating oversized chunk for embedding: chunk_id=%s", c.id)
                    c.content = " ".join(c.content.split()[: self.max_input_tokens])
                texts.append(c.content)

        vectors: Iterable[list[float]]
        if self.model:
            try:
                pending_indices = [i for i, t in enumerate(texts) if t]
                pending_texts = [texts[i] for i in pending_indices]
                pending_vectors: dict[int, list[float]] = {}
                if pending_texts:
                    encoded = self.model.encode(pending_texts, batch_size=self.batch_size, show_progress_bar=False)
                    for idx, vec in zip(pending_indices, encoded):
                        pending_vectors[idx] = vec.tolist()
                vectors = [pending_vectors.get(i, non_empty[i].embedding or self._fallback_embedding(non_empty[i].content)) for i in range(len(non_empty))]
            except Exception as exc:  # noqa: BLE001
                logger.warning("SentenceTransformer failed (%s). Falling back to hash embeddings.", exc)
                vectors = [non_empty[i].embedding or self._fallback_embedding(non_empty[i].content) for i in range(len(non_empty))]
        else:
            vectors = [non_empty[i].embedding or self._fallback_embedding(non_empty[i].content) for i in range(len(non_empty))]

        for key, chunk, emb in zip(keys, non_empty, vectors):
            chunk.embedding = emb
            self.cache.set_embedding(key, emb)
        return non_empty
