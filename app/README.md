# Embedding Retrieval System

FastAPI backend plus Streamlit frontend for:
- Phase 1 model comparison (OpenAI, Voyage AI, HuggingFace)
- Phase 3 hybrid retrieval (FAISS + BM25 + RRF + Cohere rerank)
- Phase 2 and Phase 4 notebook deliverables

## Prerequisites
- Python 3.11.x
- API keys for OpenAI, Voyage AI, and Cohere

## Install
```bash
pip install -r requirements.txt
```

## Environment
```bash
cp .env.example .env
```
Set the values in `.env`:
- `OPENAI_API_KEY`
- `VOYAGE_API_KEY`
- `VOYAGE_MODEL` (for example: `voyage-4-lite`)
- `COHERE_API_KEY`
- `APP_HOST`
- `APP_PORT`
- `LOG_LEVEL`

## Run FastAPI
```bash
uvicorn app.main:app --reload
```

## Run Streamlit
```bash
streamlit run frontend/streamlit_app.py
```

## Run Tests
```bash
pytest tests/ -v --tb=short
```

## Lint
```bash
ruff check .
```
