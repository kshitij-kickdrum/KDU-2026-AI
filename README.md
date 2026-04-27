# Multi-Modal Content Accessibility Platform

A local Streamlit application that ingests PDFs, images, and audio files, then makes them searchable and accessible with transcription/extraction, AI summaries, vector embeddings, and cost tracking.

## Features

- Upload and validate `.pdf`, `.jpg/.jpeg`, `.png`, `.mp3`, `.wav` files (100MB default max)
- PDF/image text extraction with `gpt-4o-mini` vision
- Local audio transcription with Whisper via HuggingFace Transformers
- AI summary generation (summary + key points + topic tags)
- Embedding generation with `text-embedding-3-small`
- Semantic search using FAISS (`IndexFlatL2`)
- SQLite metadata storage + JSON transcript storage
- API token/cost tracking with operation-wise breakdown
- Streamlit UI pages: Upload, Library, Search, Costs

## Project Structure

```text
src/
  core/
  models/
  services/
  storage/
  ui/
    components/
    pages/
  utils/
  config.py
  main.py
data/
  uploads/
  transcripts/
  vector_store/
tests/
  unit/
```

## Setup

1. Create and activate a Python 3.12 environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create environment file:
   ```bash
   copy .env.example .env
   ```
4. Set your OpenAI key in `.env`:
   ```env
   OPENAI_API_KEY=sk-...
   ```
   For OpenRouter testing, use:
   ```env
   OPENAI_API_KEY=your_openrouter_key
   OPENAI_BASE_URL=https://openrouter.ai/api/v1
   VISION_MODEL=openai/gpt-4o-mini
   SUMMARY_MODEL=openai/gpt-4o-mini
   EMBEDDING_MODEL=openai/text-embedding-3-small
   OPENROUTER_SITE_URL=http://localhost:8501
   OPENROUTER_APP_NAME=Content Accessibility Platform
   ```

## Run

```bash
streamlit run src/main.py
```

## Test

```bash
pytest -q
```

## Notes

- Whisper model downloads on first use.
- If `OPENAI_API_KEY` is missing, vision/summary/embedding features will fail.
- PDF vision cost can be tuned via `.env`:
  - `PDF_RENDER_SCALE` (default `1.35`)
  - `PDF_PAGE_MAX_TOKENS` (default `1200`)
  - `PDF_MAX_PAGES` (default `0`, means all pages)
- Data files and SQLite DB are persisted under `data/`.

## Known Limitations

- Single-user local app, no auth.
- Sequential processing only.
- PDF extraction currently routes through vision flow and may vary by model behavior.
- Optional UI and integration tests are not exhaustive.
