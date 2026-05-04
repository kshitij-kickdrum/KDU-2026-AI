from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import streamlit as st
from openai import OpenAI

# Ensure project root is on sys.path when launched via `streamlit run src/main.py`.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_settings
from src.core.file_manager import FileManager
from src.core.processing_manager import ProcessingManager
from src.core.search_manager import SearchManager
from src.services.audio_transcriber import AudioTranscriber
from src.services.cost_tracker import CostTracker
from src.services.embedding_generator import EmbeddingGenerator
from src.services.summary_generator import SummaryGenerator
from src.services.vision_processor import VisionProcessor
from src.storage.database import Database
from src.storage.json_storage import JsonStorage
from src.storage.vector_store import VectorStore
from src.utils.logging_config import setup_logging


st.set_page_config(page_title="Content Accessibility Platform", page_icon="A", layout="wide")


def _load_page(page_filename: str):
    path = Path(__file__).resolve().parent / "ui" / "pages" / page_filename
    spec = importlib.util.spec_from_file_location(page_filename.replace(".py", ""), path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load page module: {page_filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@st.cache_resource
def build_app() -> dict:
    settings = get_settings(validate_openai_key=False)
    setup_logging(Path("logs"), settings.log_level)

    db = Database(settings.database_path)
    db.initialize_database()

    json_storage = JsonStorage(settings.transcripts_dir)
    vector_store = VectorStore(settings.vector_store_dir)
    client_kwargs: dict = {}
    if settings.openai_api_key:
        client_kwargs["api_key"] = settings.openai_api_key
    if settings.openai_base_url:
        client_kwargs["base_url"] = settings.openai_base_url
    if settings.openrouter_site_url or settings.openrouter_app_name:
        headers = {}
        if settings.openrouter_site_url:
            headers["HTTP-Referer"] = settings.openrouter_site_url
        if settings.openrouter_app_name:
            headers["X-Title"] = settings.openrouter_app_name
        if headers:
            client_kwargs["default_headers"] = headers
    client = OpenAI(**client_kwargs)

    cost_tracker = CostTracker(db)
    embedding_generator = EmbeddingGenerator(
        client=client,
        model=settings.embedding_model,
        batch_size=settings.embedding_batch_size,
        max_retries=settings.max_retries,
        base_delay=settings.retry_base_delay,
    )
    processing_manager = ProcessingManager(
        db=db,
        json_storage=json_storage,
        vector_store=vector_store,
        vision_processor=VisionProcessor(
            client=client,
            model=settings.vision_model,
            max_retries=settings.max_retries,
            base_delay=settings.retry_base_delay,
            pdf_render_scale=settings.pdf_render_scale,
            pdf_page_max_tokens=settings.pdf_page_max_tokens,
            pdf_max_pages=settings.pdf_max_pages,
        ),
        audio_transcriber=AudioTranscriber(
            model_name=settings.whisper_model,
            device=settings.whisper_device,
        ),
        summary_generator=SummaryGenerator(
            client=client,
            model=settings.summary_model,
            max_retries=settings.max_retries,
            base_delay=settings.retry_base_delay,
        ),
        embedding_generator=embedding_generator,
        cost_tracker=cost_tracker,
    )
    search_manager = SearchManager(
        db=db,
        json_storage=json_storage,
        vector_store=vector_store,
        embedding_generator=embedding_generator,
        cost_tracker=cost_tracker,
    )

    file_manager = FileManager(
        db=db,
        uploads_dir=settings.uploads_dir,
        max_file_size_mb=settings.max_file_size_mb,
    )

    return {
        "settings": settings,
        "db": db,
        "json_storage": json_storage,
        "vector_store": vector_store,
        "file_manager": file_manager,
        "processing_manager": processing_manager,
        "search_manager": search_manager,
        "cost_tracker": cost_tracker,
    }


app = build_app()
settings = app["settings"]

if not settings.openai_api_key:
    st.warning("OPENAI_API_KEY is not set. Vision, summary and embedding features will fail.")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Upload", "Library", "Search", "Costs"])

if page == "Upload":
    page_mod = _load_page("1_upload.py")
    page_mod.render_upload_page(
        app["file_manager"],
        app["processing_manager"],
        app["cost_tracker"],
    )
elif page == "Library":
    page_mod = _load_page("2_library.py")
    page_mod.render_library_page(
        app["db"],
        app["json_storage"],
        app["file_manager"],
        app["processing_manager"],
    )
elif page == "Search":
    page_mod = _load_page("3_search.py")
    page_mod.render_search_page(app["search_manager"], app["db"])
else:
    page_mod = _load_page("4_costs.py")
    page_mod.render_costs_page(app["db"])
