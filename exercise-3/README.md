# Exercise 3 - Tri-Model AI Assistant

A local AI assistant that orchestrates three model roles:
- `BART` for chunk-level summarization
- `Qwen` (LM Studio) for merge/refine/compression/fallback
- `RoBERTa` for extractive question answering

## Features
- Paragraph-first chunking with sentence and word fallbacks
- Overlap-aware chunk merging for long documents
- Adaptive summary length (`short`, `medium`, `long`)
- Q&A fallback chain:
  1. RoBERTa on refined summary
  2. RoBERTa on base summary
  3. Qwen grounded generative fallback
  4. Structured error response
- FastAPI backend and Streamlit frontend
- In-memory session tracking with TTL cleanup

## Project Structure
- `src/api` - FastAPI app, routes, schemas, dependency container
- `src/models` - BART, Qwen, RoBERTa wrappers
- `src/services` - chunking, validation, summarization, QA, sessions
- `src/utils` - config loading, logging, token counting
- `config` - model and prompt templates
- `tests` - unit and integration tests
- `data` - sample AI/CSE/ML documents

## Setup
1. Create and activate a Python 3.12 virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start LM Studio with a Qwen chat model on `localhost:1234`.

## Run Backend
```bash
uvicorn src.api.app:app --reload --port 8000
```

## Run Streamlit UI
```bash
streamlit run src/main.py --server.port 8501
```

## API Endpoints
- `POST /api/v1/summarize`
- `POST /api/v1/refine`
- `POST /api/v1/qa`
- `GET /api/v1/health`

## Example cURL
```bash
curl -X POST http://localhost:8000/api/v1/summarize \
  -H "Content-Type: application/json" \
  -d '{"text":"<your input text, minimum 100 chars>"}'
```

## Testing
```bash
pytest -q
```

## Troubleshooting
- Qwen unavailable:
  - Verify LM Studio is running on port `1234`
  - Check API URL in `config/models.yaml`
- Slow first run:
  - HuggingFace models download on first startup
- GPU issues:
  - Set `device: "cpu"` in `config/models.yaml`

## Notes
- English plain-text input only
- Single-document summarization
- Local single-user session storage
