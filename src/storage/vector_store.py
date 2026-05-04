from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import faiss
import numpy as np


class VectorStore:
    def __init__(self, store_dir: Path, dimension: int = 1536) -> None:
        self.store_dir = store_dir
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.dimension = dimension
        self.index_path = self.store_dir / "faiss.index"
        self.metadata_path = self.store_dir / "faiss_metadata.json"
        self.index = self.initialize_index()
        self.metadata = self._load_metadata()

    def initialize_index(self):
        if self.index_path.exists():
            return faiss.read_index(str(self.index_path))
        return faiss.IndexFlatL2(self.dimension)

    def _load_metadata(self) -> dict[str, Any]:
        if self.metadata_path.exists():
            return json.loads(self.metadata_path.read_text(encoding="utf-8"))
        return {
            "index_version": "1.0",
            "dimension": self.dimension,
            "total_vectors": 0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "mappings": [],
        }

    def add_vectors(
        self,
        vectors: list[list[float]],
        embedding_ids: list[str],
        file_ids: list[str],
        chunk_indices: list[int],
    ) -> list[int]:
        if not vectors:
            return []

        start = self.index.ntotal
        arr = np.array(vectors, dtype="float32")
        self.index.add(arr)

        ids = list(range(start, start + len(vectors)))
        for i, faiss_id in enumerate(ids):
            self.metadata["mappings"].append(
                {
                    "faiss_index_id": faiss_id,
                    "embedding_id": embedding_ids[i],
                    "file_id": file_ids[i],
                    "chunk_index": chunk_indices[i],
                }
            )

        self.metadata["total_vectors"] = self.index.ntotal
        self.metadata["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.save_index()
        return ids

    def search(self, query_vector: list[float], top_k: int = 5) -> tuple[list[float], list[int]]:
        if self.index.ntotal == 0:
            return [], []
        q = np.array([query_vector], dtype="float32")
        distances, indices = self.index.search(q, top_k)
        return distances[0].tolist(), indices[0].tolist()

    def save_index(self) -> None:
        tmp_index = str(self.index_path) + ".tmp"
        tmp_meta = str(self.metadata_path) + ".tmp"

        faiss.write_index(self.index, tmp_index)
        with open(tmp_meta, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=True, indent=2)

        os.replace(tmp_index, self.index_path)
        os.replace(tmp_meta, self.metadata_path)

    def load_index(self) -> None:
        self.index = self.initialize_index()
        self.metadata = self._load_metadata()
