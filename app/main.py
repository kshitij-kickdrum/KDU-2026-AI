from contextlib import asynccontextmanager

from fastapi import FastAPI
from sentence_transformers import SentenceTransformer

from app.config import get_settings
from app.data.corpus import CHILD_STORE, PARENT_STORE
from app.routers.health import router as health_router
from app.routers.phase1 import router as phase1_router
from app.routers.phase3 import router as phase3_router
from app.services.bm25_service import BM25Service
from app.services.embedding_service import EmbeddingService
from app.services.rerank_service import RerankService
from app.services.retrieval_service import RetrievalService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    hf_model = SentenceTransformer("all-MiniLM-L6-v2")
    bm25_service = BM25Service(CHILD_STORE)
    retrieval_service = RetrievalService(CHILD_STORE, PARENT_STORE)
    embedding_service = EmbeddingService(settings=settings, hf_model=hf_model)
    rerank_service = RerankService(settings=settings)

    app.state.settings = settings
    app.state.hf_model = hf_model
    app.state.bm25_service = bm25_service
    app.state.retrieval_service = retrieval_service
    app.state.embedding_service = embedding_service
    app.state.rerank_service = rerank_service
    app.state.child_by_id = {chunk.child_id: chunk for chunk in CHILD_STORE}

    try:
        yield
    finally:
        app.state.hf_model = None


app = FastAPI(title="Embedding Retrieval System", lifespan=lifespan, docs_url="/docs")
app.include_router(health_router)
app.include_router(phase1_router)
app.include_router(phase3_router)
