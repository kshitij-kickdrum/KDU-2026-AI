from __future__ import annotations

import time
import tempfile
from pathlib import Path

import streamlit as st

from src.components.pipeline import RAGPipeline
from src.utils.config import ConfigManager
from src.utils.logging_config import configure_logging
from src.utils.monitoring import GLOBAL_METRICS


def get_pipeline() -> RAGPipeline:
    needs_init = "pipeline" not in st.session_state
    if not needs_init:
        existing = st.session_state.pipeline
        # Handle stale Streamlit session objects after code reloads.
        needs_init = not hasattr(existing, "list_documents") or not hasattr(existing, "delete_document")
    if needs_init:
        cfg = ConfigManager("config/config.yaml")
        configure_logging(cfg.get("system.log_level", "INFO"))
        st.session_state.pipeline = RAGPipeline(cfg)
    return st.session_state.pipeline


def initialize_session() -> None:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "last_query_at" not in st.session_state:
        st.session_state.last_query_at = 0.0
    if "settings" not in st.session_state:
        st.session_state.settings = {
            "top_k": 6,
            "semantic_weight": 0.6,
            "keyword_weight": 0.4,
            "temperature": 0.1,
            "max_tokens": 800,
            "chunk_size": 600,
            "chunk_overlap": 60,
        }


def apply_runtime_settings(pipeline: RAGPipeline) -> None:
    settings = st.session_state.settings
    pipeline.retriever.semantic_weight = settings["semantic_weight"]
    pipeline.retriever.keyword_weight = settings["keyword_weight"]
    pipeline.generator.temperature = settings["temperature"]
    pipeline.generator.max_tokens = settings["max_tokens"]
    pipeline.chunker.max_chunk_size = settings["chunk_size"]
    pipeline.chunker.overlap_tokens = settings["chunk_overlap"]


def app() -> None:
    st.set_page_config(page_title="Hybrid Search RAG Chatbot", layout="wide")
    initialize_session()
    st.title("Hybrid Search RAG Chatbot")
    cfg = ConfigManager("config/config.yaml")
    debug_mode = bool(cfg.get("system.debug_mode", False))
    pipeline = get_pipeline()
    apply_runtime_settings(pipeline)

    with st.sidebar:
        st.subheader("Settings")
        st.session_state.settings["top_k"] = st.slider("Top-K Chunks", 2, 12, st.session_state.settings["top_k"])
        st.session_state.settings["semantic_weight"] = st.slider(
            "Semantic Weight", 0.0, 1.0, st.session_state.settings["semantic_weight"], 0.05
        )
        st.session_state.settings["keyword_weight"] = st.slider(
            "Keyword Weight", 0.0, 1.0, st.session_state.settings["keyword_weight"], 0.05
        )
        st.session_state.settings["temperature"] = st.slider(
            "LLM Temperature", 0.0, 1.0, st.session_state.settings["temperature"], 0.05
        )
        st.session_state.settings["max_tokens"] = st.slider(
            "Max Output Tokens", 100, 1500, st.session_state.settings["max_tokens"], 50
        )
        st.session_state.settings["chunk_size"] = st.slider(
            "Chunk Size", 300, 900, st.session_state.settings["chunk_size"], 50
        )
        st.session_state.settings["chunk_overlap"] = st.slider(
            "Chunk Overlap", 0, 200, st.session_state.settings["chunk_overlap"], 10
        )
        if st.button("Reload Config", use_container_width=True):
            cfg = ConfigManager("config/config.yaml")
            errors = cfg.reload()
            if errors:
                st.error("Config issues: " + "; ".join(errors))
            else:
                st.success("Config reloaded")

        st.divider()
        st.subheader("Ingest")
        url = st.text_input("URL")
        if st.button("Ingest URL", use_container_width=True):
            try:
                with st.spinner("Fetching URL and indexing..."):
                    count = pipeline.ingest_url(url.strip())
                st.success(f"Ingested {count} chunks")
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))

        uploaded = st.file_uploader("Upload PDF", type=["pdf"])
        if uploaded and st.button("Ingest PDF", use_container_width=True):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded.getbuffer())
                tmp_path = Path(tmp.name)
            try:
                with st.spinner("Parsing PDF and indexing..."):
                    count = pipeline.ingest_pdf(
                        str(tmp_path),
                        display_title=Path(uploaded.name).stem,
                        display_source=uploaded.name,
                    )
                st.success(f"Ingested {count} chunks")
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))
            finally:
                tmp_path.unlink(missing_ok=True)

        st.divider()
        st.subheader("Documents")
        docs = pipeline.list_documents()
        if not docs:
            st.caption("No indexed documents yet.")
        for doc in docs:
            with st.expander(f"{doc['title'] or doc['document_id']} ({doc['chunk_count']} chunks)"):
                st.write(f"Source: {doc['source']}")
                if st.button(f"Delete {doc['document_id']}", key=f"del_{doc['document_id']}", use_container_width=True):
                    removed = pipeline.delete_document(doc["document_id"])
                    st.warning(f"Removed {removed} chunks")
                    st.rerun()

        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
        if debug_mode:
            with st.expander("Metrics (Debug)"):
                summary = GLOBAL_METRICS.summary()
                counters = summary.get("counters", {})
                timings = summary.get("timings_avg_ms", {})

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Ingest URL Count", counters.get("ingest_url_count", 0))
                    st.metric("Ingest PDF Count", counters.get("ingest_pdf_count", 0))
                    st.metric("Ask Count", counters.get("ask_count", 0))
                    st.metric("Ask Cache Hits", counters.get("ask_cache_hit", 0))
                with col2:
                    st.metric("Avg URL Ingest (ms)", f"{timings.get('ingest_url_ms', 0.0):.1f}")
                    st.metric("Avg PDF Ingest (ms)", f"{timings.get('ingest_pdf_ms', 0.0):.1f}")
                    st.metric("Avg Ask (ms)", f"{timings.get('ask_ms', 0.0):.1f}")

    st.subheader("Chat")
    for turn in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(turn["query"])
        with st.chat_message("assistant"):
            st.write(turn["answer"])
            with st.expander("Sources"):
                for source in turn["sources"]:
                    st.write(f"- {source}")
            if turn["warnings"]:
                st.caption(f"Warnings: {', '.join(turn['warnings'])}")

    query = st.chat_input("Ask a question about indexed documents")
    if query:
        now = time.time()
        if now - st.session_state.last_query_at < 1.5:
            st.warning("Rate limit: wait a moment before sending another query.")
            return
        st.session_state.last_query_at = now
        with st.chat_message("user"):
            st.write(query)
        with st.spinner("Retrieving and generating response..."):
            response = pipeline.ask(query=query.strip(), top_k=st.session_state.settings["top_k"])
        with st.chat_message("assistant"):
            placeholder = st.empty()
            progressive = ""
            for token in response.answer.split():
                progressive = f"{progressive} {token}".strip()
                placeholder.markdown(progressive)
            with st.expander("Sources"):
                for source in response.sources:
                    st.write(f"- {source}")
            if response.warnings:
                st.caption(f"Warnings: {', '.join(response.warnings)}")
        st.session_state.chat_history.append(
            {
                "query": query.strip(),
                "answer": response.answer,
                "sources": response.sources,
                "warnings": response.warnings,
            }
        )


if __name__ == "__main__":
    app()
