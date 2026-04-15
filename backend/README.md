# Hybrid Search RAG Chatbot (Backend, Local-Only)

## Quick Start

```powershell
cd backend
.\scripts\start_local.ps1
```

Open `http://localhost:8501`.

## Manual Run

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run src/ui/streamlit_app.py
```

## Environment Variables

Set in `.env`:

- `OPENROUTER_API_KEY` (required for LLM responses)
- `VIRUSTOTAL_API_KEY` (optional; disabled by default in local-only mode)
- `OPENROUTER_SITE_URL` (optional)
- `OPENROUTER_APP_NAME` (optional)

## Local-Only Defaults

- No cloud hosting required.
- Malware scanning API is disabled by default (`security.virustotal_enabled: false`).
- Data stays local in `backend/data/`.

## Pipeline API (Internal)

- `RAGPipeline.ingest_url(url: str) -> int`
  - Fetches URL, sanitizes, chunks, embeds, stores.
- `RAGPipeline.ingest_pdf(path: str, display_title: str | None, display_source: str | None) -> int`
  - Parses PDF, chunks, embeds, stores.
- `RAGPipeline.ask(query: str, top_k: int) -> GeneratedResponse`
  - Hybrid retrieve -> rerank -> LLM response.
- `RAGPipeline.list_documents() -> list[dict]`
- `RAGPipeline.delete_document(document_id: str) -> int`
- `RAGPipeline.backup_metadata(path: str) -> None`
- `RAGPipeline.optimize_storage() -> None`

## Testing

Fast unit suite:

```powershell
python -m pytest -q tests/unit
```

Property tests:

```powershell
python -m pytest -q tests/property
```

## Troubleshooting and FAQ

- Troubleshooting: [docs/TROUBLESHOOTING.md](/c:/Users/Dell/OneDrive/Desktop/AI/AI-5/backend/docs/TROUBLESHOOTING.md)
- FAQ: [docs/FAQ.md](/c:/Users/Dell/OneDrive/Desktop/AI/AI-5/backend/docs/FAQ.md)
- Validation report: [docs/VALIDATION_REPORT.md](/c:/Users/Dell/OneDrive/Desktop/AI/AI-5/backend/docs/VALIDATION_REPORT.md)
