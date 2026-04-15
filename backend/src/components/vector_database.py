from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from pathlib import Path
from typing import Any
import struct

from src.models import Chunk
try:
    import faiss  # type: ignore[import-untyped]
except Exception:  # noqa: BLE001
    faiss = None  # type: ignore[assignment]


class VectorDatabase:
    def __init__(self, db_path: str = "data/metadata.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._vectors: dict[str, list[float]] = {}
        self._faiss_ids: list[str] = []
        self._faiss_index = None
        self._embedding_dim = 384
        self._load_existing()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT,
                    content TEXT NOT NULL,
                    token_count INTEGER,
                    metadata_json TEXT,
                    content_hash TEXT UNIQUE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS embeddings (
                    chunk_id TEXT PRIMARY KEY,
                    embedding_blob BLOB NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    source TEXT,
                    version_hash TEXT
                )
                """
            )
            conn.commit()

    def _floats_to_blob(self, values: list[float]) -> bytes:
        return struct.pack(f"{len(values)}f", *values)

    def _blob_to_floats(self, blob: bytes) -> list[float]:
        if not blob:
            return []
        n = len(blob) // 4
        return list(struct.unpack(f"{n}f", blob))

    def _load_existing(self) -> None:
        with self._conn() as conn:
            rows = conn.execute("SELECT chunk_id, embedding_blob FROM embeddings").fetchall()
        for chunk_id, embedding_blob in rows:
            emb = self._blob_to_floats(embedding_blob)
            if emb:
                self._vectors[chunk_id] = emb
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        self._faiss_ids = list(self._vectors.keys())
        if not self._faiss_ids:
            self._faiss_index = None
            return
        if not faiss:
            return
        dim = len(self._vectors[self._faiss_ids[0]])
        self._embedding_dim = dim
        mat = [self._vectors[cid] for cid in self._faiss_ids]
        import numpy as np
        arr = np.array(mat, dtype="float32")
        faiss.normalize_L2(arr)

        if len(self._faiss_ids) >= 50:
            nlist = min(64, max(4, len(self._faiss_ids) // 8))
            quantizer = faiss.IndexFlatIP(dim)
            ivf = faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_INNER_PRODUCT)
            ivf.train(arr)
            ivf.add(arr)
            self._faiss_index = ivf
        else:
            index = faiss.IndexFlatIP(dim)
            index.add(arr)
            self._faiss_index = index

    def store_chunks(self, chunks: list[Chunk]) -> int:
        inserted = 0
        with self._conn() as conn:
            for chunk in chunks:
                if not chunk.embedding:
                    continue
                content_hash = hashlib.sha256(chunk.content.encode("utf-8")).hexdigest()
                cur = conn.execute("SELECT id FROM chunks WHERE content_hash = ?", (content_hash,))
                if cur.fetchone():
                    continue
                conn.execute(
                    """
                    INSERT INTO chunks (id, document_id, content, token_count, metadata_json, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk.id,
                        chunk.document_id,
                        chunk.content,
                        chunk.token_count,
                        json.dumps(chunk.metadata.model_dump()),
                        content_hash,
                    ),
                )
                self._vectors[chunk.id] = list(chunk.embedding)
                conn.execute(
                    "INSERT OR REPLACE INTO embeddings (chunk_id, embedding_blob) VALUES (?, ?)",
                    (chunk.id, self._floats_to_blob(chunk.embedding)),
                )
                conn.execute(
                    "INSERT OR REPLACE INTO documents (id, source, version_hash) VALUES (?, ?, ?)",
                    (chunk.document_id, chunk.metadata.document_source, content_hash),
                )
                inserted += 1
            conn.commit()
        if inserted:
            self._rebuild_index()
        return inserted

    def list_chunks(self) -> list[Chunk]:
        from src.models import ChunkMetadata

        out: list[Chunk] = []
        with self._conn() as conn:
            rows = conn.execute("SELECT id, document_id, content, token_count, metadata_json FROM chunks").fetchall()
        for chunk_id, document_id, content, token_count, metadata_json in rows:
            metadata = ChunkMetadata(**json.loads(metadata_json))
            out.append(
                Chunk(
                    id=chunk_id,
                    document_id=document_id,
                    content=content,
                    token_count=token_count,
                    start_index=0,
                    end_index=len(content),
                    metadata=metadata,
                    embedding=self._vectors.get(chunk_id),
                )
            )
        return out

    def list_documents(self) -> list[dict[str, Any]]:
        """Return unique document entries reconstructed from chunk metadata."""
        docs: dict[str, dict[str, Any]] = {}
        with self._conn() as conn:
            rows = conn.execute("SELECT document_id, metadata_json FROM chunks").fetchall()
        for document_id, metadata_json in rows:
            metadata = json.loads(metadata_json)
            title = metadata.get("document_title", "")
            source = metadata.get("document_source", "")
            if document_id not in docs:
                docs[document_id] = {
                    "document_id": document_id,
                    "title": title,
                    "source": source,
                    "chunk_count": 0,
                }
            docs[document_id]["chunk_count"] += 1
        return sorted(docs.values(), key=lambda d: d["chunk_count"], reverse=True)

    def delete_document(self, document_id: str) -> int:
        """Delete all chunks and in-memory vectors for a document."""
        removed_ids: list[str] = []
        with self._conn() as conn:
            rows = conn.execute("SELECT id FROM chunks WHERE document_id = ?", (document_id,)).fetchall()
            removed_ids = [row[0] for row in rows]
            for chunk_id in removed_ids:
                conn.execute("DELETE FROM embeddings WHERE chunk_id = ?", (chunk_id,))
            conn.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            conn.commit()
        for chunk_id in removed_ids:
            self._vectors.pop(chunk_id, None)
        if removed_ids:
            self._rebuild_index()
        return len(removed_ids)

    def similarity_search(self, query_embedding: list[float], k: int = 5) -> list[tuple[str, float]]:
        if self._faiss_index is not None and faiss:
            import numpy as np
            q = np.array([query_embedding], dtype="float32")
            faiss.normalize_L2(q)
            scores, indices = self._faiss_index.search(q, min(k, len(self._faiss_ids)))
            out: list[tuple[str, float]] = []
            for idx, score in zip(indices[0].tolist(), scores[0].tolist()):
                if idx < 0 or idx >= len(self._faiss_ids):
                    continue
                out.append((self._faiss_ids[idx], max(0.0, float(score))))
            return out

        q = query_embedding
        q_norm = math.sqrt(sum(v * v for v in q)) + 1e-8
        scored: list[tuple[str, float]] = []
        for chunk_id, vec in self._vectors.items():
            dim = min(len(vec), len(q))
            if dim == 0:
                continue
            dot = sum(vec[i] * q[i] for i in range(dim))
            v_norm = math.sqrt(sum(vec[i] * vec[i] for i in range(dim))) + 1e-8
            denom = v_norm * q_norm
            score = float(dot / denom)
            scored.append((chunk_id, max(0.0, score)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    def backup(self, backup_path: str) -> None:
        backup = Path(backup_path)
        backup.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            with sqlite3.connect(backup) as bconn:
                conn.backup(bconn)

    def optimize(self) -> None:
        with self._conn() as conn:
            conn.execute("VACUUM")
            conn.commit()
