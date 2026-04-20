from __future__ import annotations

import os
import hashlib

from src.components.contextual_chunker import ContextualChunker
from src.components.document_processor import DocumentProcessor
from src.components.embedding_generator import EmbeddingGenerator
from src.components.hybrid_retriever import HybridRetriever
from src.components.llm_generator import LLMGenerator
from src.components.reranker import Reranker
from src.components.vector_database import VectorDatabase
from src.models import GeneratedResponse
from src.utils.config import ConfigManager
from src.utils.env import load_dotenv
from src.utils.malware_scan import MalwareScanner
from src.utils.monitoring import GLOBAL_METRICS
from src.utils.cache import CacheManager


class RAGPipeline:
    def __init__(self, config: ConfigManager) -> None:
        load_dotenv()
        allowed_domains = config.get("document_processing.allowed_domains", [])
        local_only_mode = config.get("system.local_only_mode", True)
        scanner = None
        if (not local_only_mode) and config.get("security.virustotal_enabled", False):
            scanner = MalwareScanner(virustotal_api_key=os.getenv("VIRUSTOTAL_API_KEY"))
        self.doc_processor = DocumentProcessor(
            allowed_domains=allowed_domains,
            max_file_size_mb=config.get("document_processing.max_file_size_mb", 50),
            timeout_seconds=config.get("document_processing.timeout_seconds", 30),
            malware_scanner=scanner,
        )
        self.chunker = ContextualChunker(
            chunk_size=config.get("chunking.default_chunk_size", 450),
            overlap_tokens=config.get("chunking.chunk_overlap", 60),
            min_chunk_size=config.get("chunking.min_chunk_size", 100),
            max_chunk_size=config.get("chunking.max_chunk_size", 600),
            semantic_refinement_threshold=config.get("chunking.semantic_refinement_threshold", 600),
            enable_parent_child=config.get("chunking.enable_parent_child", False),
        )
        self.embedding_generator = EmbeddingGenerator(
            model_name=config.get("embeddings.model_name", "all-MiniLM-L6-v2"),
            batch_size=config.get("embeddings.batch_size", 32),
        )
        self.vector_db = VectorDatabase(db_path=config.get("storage.metadata_db_path", "data/metadata.db"))
        self.retriever = HybridRetriever(
            vector_db=self.vector_db,
            embedding_generator=self.embedding_generator,
            semantic_weight=config.get("search.semantic_weight", 0.6),
            keyword_weight=config.get("search.keyword_weight", 0.4),
            rrf_k=config.get("search.rrf_k", 60),
        )
        self.reranker = Reranker(min_relevance_threshold=config.get("search.min_relevance_threshold", 0.3))
        self.generator = LLMGenerator(
            provider=config.get("llm.provider", "openai"),
            model=config.get("llm.model", "gpt-3.5-turbo"),
            fallback_model=config.get("llm.fallback_model"),
            base_url=config.get("llm.base_url"),
            temperature=config.get("llm.temperature", 0.1),
            max_tokens=config.get("llm.max_tokens", 800),
            timeout_seconds=config.get("llm.timeout_seconds", 30),
        )
        self.cache = CacheManager()

    def ingest_url(self, url: str) -> int:
        with GLOBAL_METRICS.track("ingest_url_ms"):
            doc = self.doc_processor.process_url(url)
            chunks = self.chunker.chunk_document(doc)
            chunks = self.embedding_generator.generate_embeddings(chunks)
            inserted = self.vector_db.store_chunks(chunks)
        GLOBAL_METRICS.incr("ingest_url_count")
        return inserted

    def ingest_pdf(self, path: str, display_title: str | None = None, display_source: str | None = None) -> int:
        with GLOBAL_METRICS.track("ingest_pdf_ms"):
            doc = self.doc_processor.process_pdf_with_metadata(
                file_path=path,
                display_title=display_title,
                display_source=display_source,
            )
            chunks = self.chunker.chunk_document(doc)
            chunks = self.embedding_generator.generate_embeddings(chunks)
            inserted = self.vector_db.store_chunks(chunks)
        GLOBAL_METRICS.incr("ingest_pdf_count")
        return inserted

    def ask(self, query: str, top_k: int = 6) -> GeneratedResponse:
        qkey = hashlib.sha256(f"{query}|{top_k}".encode("utf-8")).hexdigest()
        cached = self.cache.get_query(qkey)
        if cached:
            GLOBAL_METRICS.incr("ask_cache_hit")
            return cached  # type: ignore[return-value]
        with GLOBAL_METRICS.track("ask_ms"):
            results = self.retriever.retrieve(query, k=top_k * 2)
            reranked = self.reranker.rerank_results(results, query=query)
            selected = self.reranker.fit_context_window(reranked, k=top_k)
            response = self.generator.generate_response(query, selected)
        GLOBAL_METRICS.incr("ask_count")
        self.cache.set_query(qkey, response)
        return response

    def list_documents(self) -> list[dict]:
        return self.vector_db.list_documents()

    def delete_document(self, document_id: str) -> int:
        return self.vector_db.delete_document(document_id)

    def backup_metadata(self, backup_path: str) -> None:
        self.vector_db.backup(backup_path)

    def optimize_storage(self) -> None:
        self.vector_db.optimize()
