# Validation Report

## Scope
Validation of core local-only hybrid RAG pipeline:
- document ingestion (URL/PDF),
- contextual chunking,
- embeddings + storage,
- hybrid retrieval + reranking,
- LLM generation,
- Streamlit UI flows.

## Completed Checks
- Unit tests for core models/chunker/retriever/vector-db/config/reranker/LLM/search features.
- Streamlit manual flow checks:
  - URL/PDF ingestion,
  - document listing/deletion,
  - chat interaction and source rendering.
- Config validation and reload behavior.
- Local-only mode behavior (VirusTotal disabled by default).

## Known Constraints
- If Hugging Face model download fails, system falls back to hash embeddings.
- Windows temp/cache permission locks can affect full pytest session cleanup.

## Result
Core functional requirements for local practice are met and runnable end-to-end.

