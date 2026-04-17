# FixIt AI Support System — LLMOps Implementation Plan

## Context

Building a cost-efficient LLMOps system for "FixIt" home services (plumbing/electrical/cleaning support). The current system spends $3000/month on expensive models. Goal: redesign using intelligent routing + cheap models to hit $500/month budget while maintaining >85% satisfaction.

All user decisions are confirmed. This is a local-only assignment (no cloud deployment), FastAPI REST API, Python-based.

---

## Confirmed Decisions

| Decision | Choice |
|---|---|
| LLM Provider | OpenRouter (GPT-4o-mini) + Google Gemini API (Gemini Flash Lite) |
| Interface | FastAPI REST API |
| Classification | Hybrid: rule-based first, LLM fallback if confidence < 0.70 |
| Config Storage | YAML files (external, hot-reloadable) |
| Prompt Versioning | Separate YAML files per version + `registry.yaml` |
| Cost Tracking | SQLite database (aiosqlite) |
| Budget Exceeded | Fallback ALL queries to Gemini Flash Lite (cheapest model) |
| Tests | All 4: classification, config loading, prompt versioning, cost calculation |
| Caching | Exact match cache (normalized query hash → response) stored in SQLite |
| Pre-summarization | Inputs exceeding word threshold summarized via Gemini Flash Lite before main LLM call |

### Model Tiers
| Complexity | Model | Provider |
|---|---|---|
| Low | Gemini Flash Lite | Google Gemini API |
| Medium | GPT-4o-mini | OpenRouter |
| High | GPT-4o-mini (richer prompt, more tokens) | OpenRouter |

---

## Project Structure

```
AI-5/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app factory + lifespan
│   ├── api/
│   │   ├── routes/
│   │   │   ├── query.py           # POST /query
│   │   │   ├── admin.py           # GET /admin/stats, POST /admin/config/reload, prompts
│   │   │   └── health.py          # GET /health
│   │   └── dependencies.py        # FastAPI Depends() providers
│   ├── core/
│   │   ├── config_loader.py       # YAML loading + Pydantic validation
│   │   ├── prompt_manager.py      # Load prompts, resolve versions from registry
│   │   ├── classifier.py          # Hybrid rule-based + LLM fallback classifier
│   │   ├── router.py              # Map (category, complexity) → model tier
│   │   ├── llm_client.py          # Unified async client: OpenRouter + Gemini dispatch
│   │   ├── cache.py               # Exact match cache: hash(query) → response, SQLite-backed
│   │   ├── summarizer.py          # Pre-summarization for long inputs via Gemini Flash Lite
│   │   ├── cost_tracker.py        # SQLite persistence + budget cache
│   │   └── budget_guard.py        # Budget enforcement: check + fallback logic
│   ├── models/
│   │   ├── request.py             # Pydantic request models
│   │   └── response.py            # Pydantic response models
│   └── utils/
│       └── logging.py             # Structured logging setup
├── config/
│   ├── settings.yaml              # App settings, feature flags, classifier thresholds
│   ├── models.yaml                # Model IDs, costs per token, provider config
│   ├── routing.yaml               # category + complexity → model key mapping
│   └── budget.yaml                # Daily/monthly limits, on_exceed behavior
├── prompts/
│   ├── registry.yaml              # Active version per category/role
│   ├── faq/
│   │   ├── v1.yaml
│   │   └── v2.yaml
│   ├── complaint/
│   │   ├── v1.yaml
│   │   └── v2.yaml
│   ├── booking/
│   │   ├── v1.yaml
│   │   └── v2.yaml
│   └── classifier/
│       └── v1.yaml                # Internal prompt for LLM-based classification
├── data/
│   └── costs.db                   # SQLite DB (auto-created, gitignored)
├── tests/
│   ├── conftest.py                # Fixtures: temp configs, mock LLM, in-memory DB
│   ├── test_classifier.py
│   ├── test_config_loader.py
│   ├── test_prompt_manager.py
│   └── test_cost_tracker.py
├── .env                           # API keys (gitignored)
├── .env.example
└── requirements.txt
```

---

## API Endpoints

### POST /query
```json
Request:  { "query": "str", "session_id": "str|null", "override_category": "str|null", "override_complexity": "str|null" }
Response: { "query_id": "uuid", "response": "str", "category": "str", "complexity": "str",
            "model_used": "str", "prompt_version": "str", "classification_method": "str",
            "tokens": {"prompt": int, "completion": int}, "cost_usd": float,
            "cache_hit": bool, "was_summarized": bool,
            "budget_status": {"daily_remaining_usd": float, "budget_fallback_active": bool}, "latency_ms": int }
```

### GET /admin/stats — Daily + monthly cost breakdown by category and model
### POST /admin/config/reload — Hot-reload all YAMLs without restart
### GET /admin/prompts — List registry with active + available versions
### POST /admin/prompts/activate — `{ "category": "faq", "version": "v1" }`
### GET /admin/prompts/stats — Per-version usage metrics (call count, avg latency, avg cost, cache hit rate)
### GET /health — `{ "status": "ok", "db": "ok", "config": "ok" }`

---

## Data Flow (Single Query)

```
POST /query
  │
  ▼ [1] Pydantic validation
  │
  ▼ [2] Cache.lookup(query)
  │       → Normalize query: lowercase + strip whitespace + collapse spaces
  │       → cache_key = SHA256(normalized_query)
  │       → Check response_cache table in SQLite
  │       → If HIT and not expired: return cached response immediately (cost = $0)
  │       → If MISS: continue
  │
  ▼ [3] BudgetGuard.check()
  │       → Query SQLite: SUM(cost_usd) for today + this month
  │       → If daily OR monthly limit exceeded: force model = gemini-flash-lite
  │
  ▼ [4] Classifier.classify(query)  [skipped if override_* provided]
  │       → [4a] Rule-based: keyword scoring per category, complexity heuristics
  │               If category_confidence >= 0.70 → return result (method="rule_based")
  │               Else → proceed to LLM fallback
  │       → [4b] LLM fallback: call Gemini Flash Lite with classifier prompt
  │               Parse JSON: { "category": "...", "complexity": "...", "confidence": 0.9 }
  │               On parse failure: default to (faq, low)
  │
  ▼ [5] Router.resolve(category, complexity, budget_fallback_active)
  │       → Look up routing.yaml: (category, complexity) → model_key
  │       → If budget_fallback_active → override to gemini-flash-lite
  │
  ▼ [6] Summarizer.maybe_summarize(query)
  │       → Count words in query
  │       → If word_count > threshold (default: 80 words):
  │           Call Gemini Flash Lite: "Summarize this support query in ≤40 words: {query}"
  │           Replace query with summary for prompt injection
  │           Log original_word_count, summarized_word_count
  │       → Else: pass through unchanged
  │
  ▼ [7] PromptManager.get_prompt(category)
  │       → Read registry.yaml → active version
  │       → Load prompts/{category}/{version}.yaml
  │       → Render user_template with (possibly summarized) query
  │
  ▼ [8] LLMClient.complete(model_key, system_prompt, user_message)
  │       → Dispatch: openrouter → POST openrouter.ai/api/v1/chat/completions
  │                   gemini_native → POST generativelanguage.googleapis.com/...
  │       → Retry up to 3x with exponential backoff; raise 503 on all fail
  │
  ▼ [9] Cache.store(cache_key, response, ttl)
  │       → INSERT OR REPLACE into response_cache table
  │       → ttl from settings.yaml (default: 3600s for FAQ, 0 for complaints)
  │
  ▼ [10] CostTracker.record(query_id, model_key, tokens, category)
  │       → cost = (prompt_tokens * input_rate + completion_tokens * output_rate) / 1000
  │       → INSERT INTO requests (using Decimal arithmetic)
  │       → Update in-memory budget cache
  │
  ▼ [11] Return QueryResponse JSON
```

---

## Config YAML Structure

### config/settings.yaml
```yaml
app:
  name: "FixIt AI Support System"
  version: "1.0.0"
  debug: false

feature_flags:
  enable_llm_classification_fallback: true
  enable_cost_tracking: true
  enable_budget_enforcement: true
  enable_response_cache: true
  enable_pre_summarization: true

cache:
  ttl_seconds:
    faq: 3600        # 1 hour — FAQ answers are stable
    booking: 900     # 15 min — booking availability changes
    complaint: 0     # Never cache — complaints are personal/stateful
  max_entries: 5000  # Evict LRU when exceeded

summarization:
  word_threshold: 80          # Summarize if query exceeds this word count
  target_words: 40            # Target summary length
  model: "gemini-flash-lite"  # Always use cheapest model

classification:
  rule_confidence_threshold: 0.70
  llm_fallback_model: "gemini-flash-lite"
  default_category: "faq"
  default_complexity: "low"

llm:
  request_timeout_seconds: 30
  max_retries: 3
  retry_backoff_base_seconds: 1.0

database:
  path: "data/costs.db"
  cache_budget_seconds: 60
```

### config/models.yaml
```yaml
models:
  gemini-flash-lite:
    provider: gemini_native
    model_id: "gemini-2.0-flash-lite"
    tier: low
    cost:
      input_per_1k_tokens: 0.000075
      output_per_1k_tokens: 0.000300
    params: { temperature: 0.3, max_tokens: 512 }

  gpt-4o-mini:
    provider: openrouter
    model_id: "openai/gpt-4o-mini"
    tier: medium
    cost:
      input_per_1k_tokens: 0.000150
      output_per_1k_tokens: 0.000600
    params: { temperature: 0.5, max_tokens: 1024 }

  gpt-4o-mini-high:
    provider: openrouter
    model_id: "openai/gpt-4o-mini"
    tier: high
    cost:
      input_per_1k_tokens: 0.000150
      output_per_1k_tokens: 0.000600
    params: { temperature: 0.7, max_tokens: 2048 }

providers:
  openrouter:
    base_url: "https://openrouter.ai/api/v1"
    api_key_env: "OPENROUTER_API_KEY"
  gemini_native:
    base_url: "https://generativelanguage.googleapis.com/v1beta"
    api_key_env: "GEMINI_API_KEY"
```

### config/routing.yaml
```yaml
routing_rules:
  faq:
    low: gemini-flash-lite
    medium: gpt-4o-mini
    high: gpt-4o-mini-high
  complaint:
    low: gemini-flash-lite
    medium: gpt-4o-mini
    high: gpt-4o-mini-high
  booking:
    low: gemini-flash-lite
    medium: gpt-4o-mini
    high: gpt-4o-mini-high

fallback:
  budget_exceeded_model: gemini-flash-lite
  provider_error_model: gemini-flash-lite
```

### config/budget.yaml
```yaml
budget:
  global:
    daily_limit_usd: 1.00
    monthly_limit_usd: 20.00
    on_exceed: fallback       # fallback | reject
  alerts:
    warn_at_percent: 80
```

---

## Prompt File Structure

### prompts/registry.yaml
```yaml
active_versions:
  faq:
    responder: v2
  complaint:
    responder: v2
  booking:
    responder: v1
classifier:
  active_version: v1
```

### prompts/{category}/v2.yaml (schema)
```yaml
metadata:
  version: "v2"
  category: "faq"
  role: "responder"
  created_at: "2025-01-15"
  description: "..."

prompts:
  system: |
    You are a helpful customer support agent for FixIt...
  user_template: |
    Customer question: {query}

    Provide a helpful, accurate answer.

params:
  temperature: null     # null = use model default
  max_tokens: null
```

---

## SQLite Schema

```sql
CREATE TABLE IF NOT EXISTS requests (
    id                    TEXT PRIMARY KEY,
    session_id            TEXT,
    query_text            TEXT NOT NULL,
    category              TEXT NOT NULL,
    complexity            TEXT NOT NULL,
    model_used            TEXT NOT NULL,
    prompt_version        TEXT NOT NULL,
    classification_method TEXT NOT NULL,
    prompt_tokens         INTEGER NOT NULL,
    completion_tokens     INTEGER NOT NULL,
    cost_usd              REAL NOT NULL,
    budget_fallback_active INTEGER NOT NULL,
    latency_ms            INTEGER,
    created_at            TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_requests_created_at ON requests(created_at);
CREATE INDEX IF NOT EXISTS idx_requests_category ON requests(category);

-- Response cache table
CREATE TABLE IF NOT EXISTS response_cache (
    cache_key     TEXT PRIMARY KEY,   -- SHA256(normalized_query)
    category      TEXT NOT NULL,
    response_text TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    expires_at    TEXT,               -- NULL = never expires (but complaints have ttl=0 so never stored)
    hit_count     INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON response_cache(expires_at);
```

> **Prompt usage stats** are derived by querying the `requests` table — no separate table needed:
> ```sql
> SELECT prompt_version, COUNT(*) as uses, AVG(latency_ms) as avg_latency_ms,
>        AVG(cost_usd) as avg_cost_usd
> FROM requests
> WHERE category = 'faq'
> GROUP BY prompt_version;
> ```
> `GET /admin/prompts/stats` runs this per category and returns the aggregated result.

---

## Classifier Logic

### Rule-Based (first pass)
- **Category scoring**: keyword dictionaries with weights per category (faq/complaint/booking)
  - High-weight (1.0): "refund", "complaint", "hours", "book", "reschedule", etc.
  - Medium-weight (0.6): "problem", "issue", "question", "schedule", etc.
  - `confidence = score(winner) / (score(winner) + sum(others) + ε)`
- **Complexity scoring**: heuristics
  - word_count: <15→low, 15–40→medium, >40→high
  - urgency keywords ("urgent", "asap", "emergency") → bump up one tier
  - negation count ("didn't", "never", "won't" > 2) → bump up one tier
- **Gate**: if `category_confidence >= 0.70` → return result; else → LLM fallback

### LLM Fallback (second pass)
- Always uses Gemini Flash Lite (cheapest), even when budget enforcement is active
- Sends classifier system prompt from `prompts/classifier/v1.yaml`
- Expects strict JSON: `{"category": "...", "complexity": "...", "confidence": 0.9}`
- Strip markdown fences, use regex fallback before `json.loads()`
- On parse failure after 1 retry: default to `(faq, low, method="llm_fallback_parse_error")`

---

## Test Strategy

### conftest.py fixtures
- `tmp_config_dir` — writes minimal valid YAMLs to `tmp_path`
- `in_memory_db` — `aiosqlite.connect(":memory:")` per test, never touches disk
- `mock_llm` — `mocker.patch("app.core.llm_client.LLMClient._call_openrouter")` returning fake `LLMResponse`
- `sample_queries` — dict of query strings → expected outcomes for parametrize

### test_classifier.py
- Rule-based: clear FAQ/complaint/booking → correct category; low-confidence → triggers fallback
- Complexity: short query → low; long multi-part → high; urgency keywords → bump up
- LLM fallback: mock LLM returns JSON → parsed correctly; mock LLM returns garbage → defaults used
- Overrides: `override_category` bypasses classifier entirely

### test_config_loader.py
- Valid YAMLs load without error (all four config files)
- Missing required field raises Pydantic `ValidationError`
- Negative budget raises validation error
- Hot-reload: write modified YAML to `tmp_path`, reload, assert new value returned
- Feature flag disabled → LLM fallback never called (even at low confidence)

### test_prompt_manager.py
- Active version resolved from registry
- Explicit version overrides registry
- Missing version file raises `FileNotFoundError`
- `user_template` renders with `{query}` correctly
- Query with literal `{` is escaped before formatting (no `KeyError`)
- Activating non-existent version raises error

### test_cost_tracker.py
- Cost = `(prompt_tokens * input_rate + completion_tokens * output_rate) / 1000` (exact decimal)
- Zero tokens → zero cost
- Records are persisted and queryable from in-memory DB
- Daily/monthly aggregates computed correctly across multiple inserts
- Budget exceeded → `budget_fallback_active = True` returned by `BudgetGuard`
- Budget cache: SQLite only queried once per N requests within cache window

---

## Implementation Sequence

1. Scaffold all directories + `__init__.py` + `requirements.txt` + `.env.example`
2. Write all YAML configs (`config/` + `prompts/`) — source of truth first
3. `config_loader.py` + `test_config_loader.py` → all tests pass
4. `prompt_manager.py` + `test_prompt_manager.py` → all tests pass
5. `llm_client.py` (OpenRouter + Gemini dispatch, retry logic)
6. `classifier.py` + `test_classifier.py` → all tests pass
7. `cost_tracker.py` + `budget_guard.py` + `test_cost_tracker.py` → all tests pass
8. `cache.py` (SQLite-backed exact match cache, TTL per category, LRU eviction)
9. `summarizer.py` (word count check → Gemini Flash Lite summarization call)
10. `router.py` (thin: classification + routing table lookup)
11. `main.py` + route handlers + `dependencies.py` (wire everything via `app.state`)
12. Run `pytest`, then `uvicorn app.main:app --reload`, test manually with curl/HTTPie

---

## Critical Files

- [app/core/classifier.py](app/core/classifier.py) — Most complex: rule engine + LLM fallback dispatch, confidence gate
- [app/core/llm_client.py](app/core/llm_client.py) — Provider adapter for OpenRouter (Bearer auth) + Gemini (query param API key)
- [app/core/cost_tracker.py](app/core/cost_tracker.py) — SQLite + budget cache; correctness affects every component
- [config/models.yaml](config/models.yaml) — Source of truth for costs; all cost calculations derive from here
- [tests/conftest.py](tests/conftest.py) — Foundation for all 4 test files; poor design here forces rewrites

## Key Gotchas

1. **Gemini API key** is a query param (`?key=API_KEY`), NOT a Bearer header like OpenRouter
2. **SQLite + async**: use `aiosqlite`, not `sqlite3`, inside async FastAPI handlers; pass `check_same_thread=False` only if using sync sqlite3 in a thread pool
3. **Prompt injection safety**: escape `{` and `}` in user query before `str.format_map()`
4. **Cost arithmetic**: use Python `Decimal`, not `float`, to avoid drift across 10k queries/day
5. **FastAPI lifespan**: use `@asynccontextmanager lifespan(app)` not deprecated `@app.on_event("startup")`
6. **LLM JSON parsing**: strip markdown fences + regex fallback before `json.loads()` on classifier response

## Local Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Client (curl / UI)                    │
└────────────────────────────┬────────────────────────────────┘
                             │ POST /query
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI (uvicorn)                        │
│                                                             │
│  ┌──────────┐   HIT ──────────────────────────────────────► │ response
│  │  Cache   │◄──────────────────────────────────────────────┤
│  │(SQLite)  │   MISS                                        │
│  └──────────┘    │                                          │
│                  ▼                                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              BudgetGuard                             │   │
│  │  reads daily/monthly spend from SQLite               │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Hybrid Classifier                       │   │
│  │  [Rule-based] ──low confidence──► [LLM fallback]    │   │
│  │       ↓                           Gemini Flash Lite  │   │
│  │  category + complexity                               │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         ▼                                   │
│            ┌────────────────────────┐                       │
│            │        Router          │                       │
│            │ routing.yaml lookup    │                       │
│            └────────────┬───────────┘                       │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Summarizer (optional)                     │   │
│  │  if query > 80 words → Gemini Flash Lite summary    │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            PromptManager                             │   │
│  │  registry.yaml → load prompts/{cat}/{ver}.yaml      │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              LLMClient                               │   │
│  │  ┌─────────────────┐   ┌───────────────────────┐    │   │
│  │  │  OpenRouter API │   │  Google Gemini API    │    │   │
│  │  │  (GPT-4o-mini)  │   │  (Gemini Flash Lite)  │    │   │
│  │  └─────────────────┘   └───────────────────────┘    │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         ▼                                   │
│  ┌────────────────┐  ┌──────────────────────────────────┐   │
│  │  Cache.store() │  │       CostTracker                │   │
│  │  (SQLite TTL)  │  │  INSERT into requests (SQLite)   │   │
│  └────────────────┘  └──────────────────────────────────┘   │
│                                                             │
│  Config layer (read at startup, hot-reloadable):            │
│  settings.yaml · models.yaml · routing.yaml · budget.yaml   │
└─────────────────────────────────────────────────────────────┘
```

---

## Cost Analysis: Before vs After Optimization

### Before (Current System)
Assumptions: all 10,000 queries/day sent to a single expensive model (GPT-4o equivalent).

| Item | Value |
|---|---|
| Queries/day | 10,000 |
| Queries/month | 300,000 |
| Avg tokens/query (in + out) | ~600 (400 input + 200 output) |
| GPT-4o price | $5.00 input / $15.00 output per 1M tokens |
| Cost/query | (400 × $0.005 + 200 × $0.015) / 1000 = **$0.0050** |
| **Monthly cost** | 300,000 × $0.0050 = **$1,500–$3,000/month** |

### After (Our System)

**Query distribution assumption** (based on sample data):
- 60% FAQ / low → Gemini Flash Lite
- 25% Booking / medium → GPT-4o-mini
- 15% Complaint / high → GPT-4o-mini (richer prompt)

**Cache hit rate assumption**: ~30% of FAQ queries are repeated → 18% of all queries served from cache at $0.

| Tier | % of queries | Effective % (post-cache) | Model | Input cost /1k | Output cost /1k | Avg tokens | Cost/query |
|---|---|---|---|---|---|---|---|
| Gemini Flash Lite (FAQ low) | 60% | 42% | gemini-flash-lite | $0.000075 | $0.000300 | 400+150 | **$0.000075** |
| GPT-4o-mini (medium) | 25% | 25% | gpt-4o-mini | $0.000150 | $0.000600 | 500+300 | **$0.000255** |
| GPT-4o-mini (high) | 15% | 15% | gpt-4o-mini | $0.000150 | $0.000600 | 600+500 | **$0.000390** |
| Cache hit | 18% of total | — | none | — | — | 0 | **$0.000000** |

**Weighted avg cost/query:**
```
= (0.42 × $0.000075) + (0.25 × $0.000255) + (0.15 × $0.000390) + (0.18 × $0)
= $0.0000315 + $0.0000638 + $0.0000585 + $0
≈ $0.000154 per query
```

**Monthly cost:**
```
300,000 queries × $0.000154 = ~$46/month
```

| Metric | Before | After | Saving |
|---|---|---|---|
| Monthly cost | ~$1,500–3,000 | **~$46** | **97–98%** |
| Cost/query | ~$0.005 | **~$0.000154** | **97%** |
| Budget target | $500/month | $46/month | Well within budget |

> **Note**: Pre-summarization reduces token count for long inputs by ~50%, further decreasing cost for the 15% of high-complexity queries that typically have verbose context.

---

## Verification

```bash
# Install
pip install -r requirements.txt
cp .env.example .env   # fill in OPENROUTER_API_KEY + GEMINI_API_KEY

# Run tests (no real API calls — all mocked)
pytest tests/ -v

# Start server
uvicorn app.main:app --reload

# Test manually
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are your hours?"}'

curl http://localhost:8000/admin/stats
curl http://localhost:8000/admin/prompts
```

---

## Future AWS Architecture (Scalable Production)

> **Current deployment**: Local only. The following describes AWS services that would replace each local component in a production-scale architecture.

| Local Component | AWS Replacement | Rationale |
|---|---|---|
| `uvicorn` (FastAPI process) | **AWS Lambda** + API Gateway | Serverless, scales to 10k+ req/day with zero idle cost; Lambda's 15-min timeout is sufficient for LLM calls |
| `config/*.yaml` files | **AWS S3** (+ optional Parameter Store for secrets) | YAML files stored in S3; hot-reload fetches from S3 on config change. Parameter Store for API keys instead of `.env` |
| `prompts/` YAML files | **AWS S3** | Prompt files stored in S3 with versioning enabled — S3 object versioning replaces manual `v1.yaml`/`v2.yaml` files |
| `data/costs.db` (SQLite) | **AWS RDS (PostgreSQL)** or **DynamoDB** | RDS for relational cost queries (daily/monthly aggregates). DynamoDB if schema-less per-request logs are preferred at scale |
| In-memory budget cache + `response_cache` SQLite table | **AWS ElastiCache (Redis)** | Redis covers both: budget totals (shared across Lambda instances) and response cache (hash → response, with TTL per category). Local SQLite cache becomes a Redis `SETEX` call. |
| `uvicorn --reload` hot config | **AWS AppConfig** | Managed config service with rollout strategies, rollback, and change monitoring — replaces manual `POST /admin/config/reload` |
| Structured logs (`logging.py`) | **AWS CloudWatch Logs** | Lambda logs automatically stream to CloudWatch; add metric filters for cost alerts and budget threshold alarms |
| Classifier LLM fallback calls | **AWS Bedrock** | Could replace OpenRouter/Gemini with Bedrock-hosted models (e.g., Titan, Claude) for VPC-native calls with IAM auth and no external API keys |

### Architecture Diagram (Future State)

```
Client
  │
  ▼
API Gateway (REST)
  │
  ▼
AWS Lambda (FastAPI via Mangum adapter)
  ├── reads config from S3
  ├── reads prompts from S3
  ├── reads budget cache from ElastiCache (Redis)
  │
  ├── calls OpenRouter / Gemini (external)
  │     └── OR AWS Bedrock (VPC-native alternative)
  │
  ├── writes request log → RDS PostgreSQL
  └── updates budget cache → ElastiCache

CloudWatch Logs ← Lambda stdout
CloudWatch Alarms ← budget threshold metrics
AWS Parameter Store ← API keys (OPENROUTER_API_KEY, GEMINI_API_KEY)
```

### Why Not EC2?

EC2 would work but is always-on billing. At 10,000 queries/day (~7 req/min average), Lambda's pay-per-invocation model costs significantly less than a running EC2 instance. EC2 makes sense only if latency requirements demand persistent warm connections to the DB or cache.
