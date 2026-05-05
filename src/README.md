# AgentKit Orchestration

Multi-agent orchestration lab implementation using the OpenAI Agents SDK, SQLite, and Streamlit.

The system demonstrates:

- loop detection with a circuit breaker
- LLM-driven tool selection through isolated SDK agents
- Coordinator to Finance and HR delegation
- structured context payloads without full-history handoff
- persistent session memory and case-fact extraction
- long-document ingestion with local preprocessing before LLM calls
- planner-executor workflow with persisted execution steps

## Setup

Use Python 3.11 or newer.

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. `OPENROUTER_API_KEY` is optional and used as a fallback when configured.

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
notepad .env
```

Make sure the file is named exactly `.env`, not `.env.txt`.

Prompts and model/budget settings live in:

- `config/prompts.yml`
- `config/models.yml`

Secrets stay in `.env`.

## Run

```bash
python -m src.scripts.init_db
streamlit run src/ui/streamlit_app.py
```

You can also initialize the database by constructing `OrchestrationEngine`; it creates the schema automatically.

## Main API

```python
from src.core.orchestration_engine import OrchestrationEngine

engine = OrchestrationEngine()
result = engine.process_query("What is John's salary and how much PTO does he have?")
print(result["response"])
```

The response contains `session_id`, `response`, `state`, `token_count`, `case_facts`, `missing_fields`, and optional compaction/error details.

## Phase Usage

Phase 1:

```text
Count the active users
```

The loop demo agent uses `o3-mini` and a failing `query_internal_database` tool. The circuit breaker opens after 3 failures and returns a graceful fallback.

Phase 2:

```text
What is John's salary and how much PTO does he have?
```

The Coordinator has only delegation tools. The LLM decides whether to call Finance and HR delegation tools. Finance and HR only see their own domain tools.

Phase 3:

```text
Update my banking details. Routing number is 123456789.
```

The coordinator builds a structured context payload. Full chat history is not transferred to the sub-agent. Missing required fields are tracked in SQLite.

Phase 4:

Paste a long document with transaction/order/invoice IDs, amounts, dates, and names. If it exceeds the configured word/token threshold, the system extracts case facts locally first, persists them, and compacts memory without repeatedly sending the raw document to agents.

Phase 5:

```text
/plan Analyze sales data and generate a report
```

The Planner uses `o3-mini` to generate structured JSON. The Executor uses `gpt-4o-mini` by default and persists each step result before proceeding.

## Token And Rate Controls

Configured in `config/models.yml`, with optional `.env` overrides:

- `MAX_INPUT_TOKENS`
- `MAX_OUTPUT_TOKENS`
- `MAX_AGENT_TURNS`
- `MEMORY_TOKEN_THRESHOLD`
- `LONG_DOCUMENT_WORD_THRESHOLD`
- `COMPACTION_CHUNK_TOKENS`
- `RATE_LIMIT_MAX_RETRIES`

Before each SDK run, the system estimates input tokens and fails fast if the request exceeds budget. SDK runs also use `max_turns` to stop loops.

## Notes

Automated tests are intentionally not included yet, per the requested scope. Smoke checks should verify config loading, schema initialization, module imports, and SDK availability.
