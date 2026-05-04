from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


class FAISSStore:
    def __init__(self, index_path: str | Path, metadata_path: str | Path) -> None:
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self.index: Any | None = None
        self.metadata: dict[str, Any] = {}
        self.disabled = False

    def load(self) -> None:
        try:
            import faiss

            self.index = faiss.read_index(str(self.index_path))
            self.metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except Exception:
            self.disabled = True
            self.index = None
            self.metadata = {}

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if self.index is None:
            self.load()
        if self.disabled or self.index is None:
            return self._metadata_fallback(query, top_k)
        vector = self.embed(query)
        distances, indices = self.index.search(vector, top_k)
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            item = dict(self.metadata.get(str(int(idx)), {}))
            item["score"] = float(distance)
            results.append(item)
        return results

    @staticmethod
    def embed(text: str, dimensions: int = 384) -> np.ndarray:
        vector = np.zeros((1, dimensions), dtype=np.float32)
        for pos, byte in enumerate(text.encode("utf-8")):
            vector[0, pos % dimensions] += byte / 255.0
        norm = np.linalg.norm(vector)
        if norm:
            vector /= norm
        return vector

    def _metadata_fallback(self, query: str, top_k: int) -> list[dict[str, Any]]:
        if not self.metadata_path.exists():
            return []
        self.metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        terms = set(query.lower().split())
        scored = []
        for item in self.metadata.values():
            text = f"{item.get('title', '')} {item.get('content_preview', '')}".lower()
            score = sum(1 for term in terms if term in text)
            scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [dict(item, score=float(score)) for score, item in scored[:top_k]]

