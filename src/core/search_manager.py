from __future__ import annotations

from src.models.search_models import SearchResponse, SearchResult
from src.services.cost_tracker import CostTracker
from src.services.embedding_generator import EmbeddingGenerator
from src.storage.database import Database
from src.storage.json_storage import JsonStorage
from src.storage.vector_store import VectorStore


class SearchManager:
    def __init__(
        self,
        db: Database,
        json_storage: JsonStorage,
        vector_store: VectorStore,
        embedding_generator: EmbeddingGenerator,
        cost_tracker: CostTracker,
    ) -> None:
        self.db = db
        self.json_storage = json_storage
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.cost_tracker = cost_tracker

    @staticmethod
    def _distance_to_similarity(distance: float) -> float:
        return max(0.0, min(1.0, 1.0 / (1.0 + distance)))

    def semantic_search(
        self, query: str, top_k: int = 5, file_ids: list[str] | None = None
    ) -> SearchResponse:
        if top_k < 1 or top_k > 20:
            raise ValueError("top_k must be between 1 and 20")

        query_vector, tokens = self.embedding_generator.create_query_embedding(query)
        log = self.cost_tracker.log_api_call(
            operation_type="embedding",
            model_name="text-embedding-3-small",
            input_tokens=tokens,
            output_tokens=0,
            file_id=None,
            metadata={"stage": "search_query"},
        )

        distances, faiss_ids = self.vector_store.search(query_vector, top_k=top_k)
        if not faiss_ids:
            return SearchResponse(results=[], query_tokens_used=tokens, query_cost_usd=log.cost_usd)

        rows = self.db.get_embeddings_by_faiss_ids([fid for fid in faiss_ids if fid >= 0])
        by_faiss = {row["faiss_index_id"]: row for row in rows}

        results: list[SearchResult] = []
        for idx, faiss_id in enumerate(faiss_ids):
            if faiss_id < 0 or faiss_id not in by_faiss:
                continue
            embed_row = by_faiss[faiss_id]
            if file_ids and embed_row["file_id"] not in file_ids:
                continue

            file_row = self.db.get_file(embed_row["file_id"])
            if not file_row:
                continue

            transcript = self.json_storage.load_transcript(embed_row["file_id"])
            full_text = transcript["transcript"].get("cleaned_text", "")
            start = int(embed_row["chunk_start_char"])
            end = int(embed_row["chunk_end_char"])
            context_before = full_text[max(0, start - 50) : start]
            context_after = full_text[end : end + 50]

            results.append(
                SearchResult(
                    chunk_text=embed_row["chunk_text"],
                    file_id=embed_row["file_id"],
                    filename=file_row["filename"],
                    file_type=file_row["file_type"],
                    similarity_score=round(self._distance_to_similarity(float(distances[idx])), 4),
                    context_before=context_before,
                    context_after=context_after,
                    chunk_index=int(embed_row["chunk_index"]),
                )
            )

        return SearchResponse(results=results, query_tokens_used=tokens, query_cost_usd=log.cost_usd)
