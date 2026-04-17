# KDU Coursework — AI Assessments

This repository contains AI assessment submissions.

Each assessment is developed on its own branch (e.g. `AI-5`, `AI-6`) and merged into `main` via pull request.

## Branch Structure

| Branch | Description |
|---|---|
| `main` | Base branch — all assessment branches are created from here |
| `AI-5` | FastAPI Production Template |
| `AI-6` | Multimodal AI Assistant |
| `AI-7` | Stock Trading Agent & Agent Meets Analytics |
| `AI-8` | Hybrid Search RAG Chatbot |
| `AI-9` | MCP and Tool Integration |
| `AI-10` | LLMOps for FixIt AI Support System |

## FixIt AI Support System (AI-10)

This branch now includes a full FastAPI implementation of the FixIt AI Support System with:

- YAML-driven configuration and prompt registry
- Hot-reload support for config and prompt versions
- Hybrid query classification and model routing
- Multi-provider LLM client (OpenRouter + Gemini) with retry backoff
- SQLite-backed cache and cost tracking
- Budget enforcement with warning thresholds
- Admin endpoints, health checks, and integration tests

### Quick start

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```
