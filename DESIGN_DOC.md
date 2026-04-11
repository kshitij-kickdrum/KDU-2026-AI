# Multimodal AI Assistant — Design Document

---

## 1. Overview

A LangChain-powered AI agent that handles text and image inputs, personalizes responses from a stored user profile, maintains session memory, enforces structured JSON output, and dynamically switches models and communication styles based on task type. Exposed via a FastAPI REST API.

**Out of scope:** Frontend, user authentication, streaming responses, long-term vector memory, production infrastructure.

---

## 2. Tech Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Language | Python 3.11+ | Async support, LangChain ecosystem |
| Web Framework | FastAPI | Auto docs, Pydantic built-in, async-first |
| AI Framework | LangChain | Pre-built agent, memory, tool, and parser abstractions |
| LLM (Text) | GPT-4o | Best-in-class reasoning, function-calling support |
| LLM (Vision) | GPT-4o (vision) | Same model handles image understanding natively |
| Intent Classifier | GPT-4o-mini | Lightweight model for fallback intent classification — keyword match is always tried first |
| Output Parsing | LangChain PydanticOutputParser | Schema validation and type coercion without manual logic |
| Memory | LangChain ConversationBufferMemory | Simple in-memory chat history, zero infra |
| Validation | Pydantic v2 | Built into FastAPI, strict request/response schemas |
| Config | pydantic-settings | Reads from `.env`, type-safe, no manual `os.getenv` |
| HTTP Client | httpx | Async external API calls (weather) |
| Testing | pytest + pytest-asyncio | Async test support |
| Logging | structlog (JSON) | Structured, parseable logs |

---

## 3. Project Structure

Service-based structure — each concern (agent, tools, memory, parsers) lives in its own module. Adding a new tool means adding one file in `tools/` and registering it in `agent.py`.

```
ai-assistant/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py              # POST /chat
│   │   │   ├── image.py             # POST /image
│   │   │   ├── history.py           # GET /history
│   │   │   ├── session.py           # DELETE /session
│   │   │   ├── user.py              # GET /user/{user_id}
│   │   │   └── health.py            # GET /health
│   │   └── dependencies.py          # Shared FastAPI deps (session loader, profile loader)
│   │
│   ├── agent/
│   │   ├── agent.py                 # Builds and runs the LangChain agent
│   │   ├── router.py                # Routes input: text → agent, image → vision pipeline
│   │   └── style.py                 # Builds Expert / Child system prompt prefix
│   │
│   ├── tools/
│   │   └── weather_tool.py          # @tool — fetches or mocks weather by city
│   │
│   ├── memory/
│   │   └── session_memory.py        # Dict of session_id → ConversationBufferMemory
│   │
│   ├── parsers/
│   │   ├── weather_parser.py        # Pydantic schema + PydanticOutputParser for weather
│   │   ├── image_parser.py          # Pydantic schema + parser for image response
│   │   ├── chat_parser.py           # Pydantic schema + parser for general chat
│   │   └── retry.py                 # Retry chain: re-prompts LLM on parse failure
│   │
│   ├── prompts/
│   │   ├── system_prompt.py         # Base system prompt template
│   │   └── personalization.py       # Injects user profile fields into prompt
│   │
│   ├── models/
│   │   ├── request_models.py        # ChatRequest, ImageRequest, SessionRequest
│   │   └── response_models.py       # ChatResponse, ImageResponse, HistoryResponse
│   │
│   ├── services/
│   │   ├── chat_service.py          # Orchestrates: profile → memory → agent → parse
│   │   ├── image_service.py         # Orchestrates: encode → vision LLM → parse
│   │   ├── postprocessor.py         # Normalizes response envelope before returning to client
│   │   └── user_service.py          # Loads user profile from data/user_profiles.json
│   │
│   ├── middleware/
│   │   └── context_middleware.py    # Input validation · request_id generation · logging · profile loading
│   │
│   ├── data/
│   │   ├── user_profiles.json       # Mock user profiles keyed by user_id
│   │   └── mock_weather.json        # Mock weather data keyed by city name
│   │
│   └── core/
│       ├── config.py                # Settings class (pydantic-settings, reads .env)
│       ├── exceptions.py            # AppException base + domain subclasses
│       └── logging.py               # structlog setup
│
├── tests/
│   ├── conftest.py                  # Fixtures: test client, mock profiles, mock memory
│   ├── test_chat.py
│   ├── test_image.py
│   ├── test_memory.py
│   ├── test_parser.py
│   └── test_tools.py
│
├── .env
├── .env.example
├── requirements.txt
└── main.py                          # App init, router registration, lifespan
```

---

## 4. Architecture

```
┌──────────────────────────────────────────────────────────┐
│                         CLIENT                            │
└─────────────────────────┬────────────────────────────────┘
                          │ HTTP
                          ▼
┌──────────────────────────────────────────────────────────┐
│                      FastAPI Layer                        │
│    /chat    /image    /history    /session    /health     │
└─────────────────────────┬────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│                   Middleware / Router                      │
│   Detects input type · Loads user profile · Picks style  │
└────┬──────────────────┬──────────────────┬───────────────┘
     │                  │                  │
     ▼                  ▼                  ▼
┌─────────┐    ┌─────────────────┐   ┌────────────┐
│ Memory  │◄──►│ LangChain Agent │──►│ WeatherTool│
│ Layer   │    │  (Orchestrator) │   └────────────┘
└─────────┘    └────────┬────────┘
                        │
               ┌────────┴─────────┐
               ▼                  ▼
         ┌──────────┐      ┌─────────────┐
         │ Text LLM │      │  Vision LLM │
         │ (GPT-4o) │      │  (GPT-4o)   │
         └────┬─────┘      └──────┬──────┘
              └────────┬──────────┘
                       ▼
               ┌───────────────┐
               │ Output Parser │  ← validates JSON schema, retries on failure
               └───────┬───────┘
                       ▼
               ┌───────────────────┐
               │  Post-processing  │  ← normalizes response envelope
               └─────────┬─────────┘
                         ▼
              Structured JSON → Client
```

---

## 5. Components

### Agent & Routing

The router in `agent/router.py` checks the input before touching the agent:
- If the request contains an image → skip the agent, send directly to the Vision LLM pipeline
- If the request is text → pass to the LangChain agent

**Agent type:** `OPENAI_FUNCTIONS`. Function-calling is more reliable than ReAct string parsing for tool selection — fewer hallucinated tool calls, consistent output format.

**Intent classification strategy (cost-saving):**

Before the agent runs, the router classifies the intent using a two-step fallback:
1. **Keyword check first** — scan for hardcoded signals (e.g. image attachment → vision pipeline; "weather", "temperature", "forecast" → WeatherTool)
2. **LLM fallback if no match** — if no keyword matches, call GPT-4o-mini (not GPT-4o) to interpret intent

This avoids burning expensive GPT-4o tokens on simple classification. A reasoning model is overkill for deciding "is this a weather query?" — GPT-4o-mini is sufficient unless the prompt is genuinely ambiguous.

**ReAct loop (text path):**
```
Query → Think (tool needed?) → [Tool call → Observation] → Think → Final Answer → Parser
```

**Tool registered with the agent:**

```python
@tool
def get_weather(location: str) -> str:
    """Fetches current weather data for the given location."""
    ...
```

The agent calls `get_weather` when the query is about weather or conditions. The user's location comes from their profile — the agent never asks the user for it.

---

### Personalization

On every request, `context_middleware.py` loads the user profile from `data/user_profiles.json` and attaches it to the request state. `personalization.py` then builds a context block injected into the system prompt.

Profile shape:
```json
{
  "user_id": "u_001",
  "name": "Riya",
  "location": "Mumbai, India",
  "timezone": "Asia/Kolkata",
  "preferred_style": "expert"
}
```

The LLM receives name, location, and timezone in every call. It never asks the user to repeat this information.

**Location priority:** If the user states a location in their message (e.g. "what's the weather in Delhi?"), that takes precedence over the profile's stored location. The profile location is only the default fallback when no location is mentioned in the query.

---

### Communication Style

`style.py` reads `preferred_style` from the user profile (or a per-request override) and prepends a style block to the system prompt.

| Style | Behavior |
|-------|----------|
| `expert` | Technical language, concise, no hand-holding |
| `child` | Simple words, friendly tone, analogies, no jargon |

Style can be overridden per-request via the `style` field in the request body. Profile default applies if omitted.

---

### Structured Output

Every LLM response is validated against a Pydantic schema via `PydanticOutputParser`. The parser appends format instructions to the prompt automatically — no manual JSON prompting needed.

On `OutputParserException`, `retry.py` re-prompts the LLM with the parse error and the bad output. Max 2 retries. Returns HTTP 422 if exhausted.

Response schemas live in `parsers/`. Each response type (weather, image, chat) has its own Pydantic model.

---

### Memory

Session memory is a module-level dict in `session_memory.py`:

```python
_store: dict[str, ConversationBufferMemory] = {}
```

Keyed by `session_id`. On each request, the session's history is loaded and appended to the prompt. If a `session_id` is not found, a fresh empty memory is created automatically. Memory is cleared on `DELETE /session`.

User profile is **not** memory — it is static context loaded fresh on every request, not part of the conversation history.

**Memory is not a database.** `ConversationBufferMemory` is in-memory and intentionally temporary. Do not replace it with database reads per turn — the overhead defeats the purpose of a fast conversational loop. If persistence across restarts is needed, that is a future improvement (Redis), not a v1 requirement.

---

### Image Pipeline

Image requests bypass the agent entirely. Flow:

```
Upload (JPEG/PNG/WEBP) → base64 encode → GPT-4o vision → description text → ImageParser → JSON
```

The vision model returns a structured description wrapped in the `ImageResponse` schema. The agent is not involved.

---

### Post-processing

`postprocessor.py` runs after the parser on every request path (text and image) before the response is returned to the client. It normalizes the output into a consistent response envelope regardless of which tool or model produced it.

This layer exists because different input types (text, image, future: audio) produce structurally different internal responses. The post-processor ensures the client always receives the same top-level shape:

```json
{
  "session_id": "...",
  "response": { ... },
  "model_used": "...",
  "tool_used": "...",
  "style_applied": "..."
}
```

Tool-specific data goes inside `response`. The envelope never changes. This keeps downstream consumers stable when new tools are added.

---

## 6. API Endpoints

**Base URL:** `http://localhost:8000/api/v1`

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/chat` | Send a text query | No |
| POST | `/image` | Upload an image for analysis | No |
| GET | `/history` | Get session conversation history | No |
| DELETE | `/session` | Clear session memory | No |
| GET | `/user/{user_id}` | Get user profile | No |
| GET | `/health` | Health check | No |

**Standard error response** — every error across all endpoints returns this shape:
```json
{ "code": "USER_NOT_FOUND", "message": "No user found with id u_999." }
```

---

### POST /chat

```json
// Request
{
  "user_id": "u_001",
  "session_id": "sess_abc123",
  "message": "What's the weather like today?",
  "style": "expert"
}

// Response 200
{
  "session_id": "sess_abc123",
  "response": {
    "temperature": "32°C",
    "summary": "Hot and humid with partial clouds",
    "location": "Mumbai, India",
    "feels_like": "36°C",
    "advice": "Stay hydrated"
  },
  "tool_used": "WeatherTool",
  "model_used": "gpt-4o",
  "style_applied": "expert"
}
```

| Status | Code | Reason |
|--------|------|--------|
| 400 | INVALID_REQUEST | Missing required fields or blank message |
| 404 | USER_NOT_FOUND | `user_id` not in profiles |
| 422 | PARSE_ERROR | JSON parse failed after 2 retries |
| 500 | INTERNAL_ERROR | Unexpected server error |

---

### POST /image

```
// Request: multipart/form-data
user_id    string  required
session_id string  required
image      file    required   JPEG, PNG, WEBP — max 10MB
prompt     string  optional   e.g. "What objects are present?"

// Response 200
{
  "session_id": "sess_abc123",
  "response": {
    "description": "A golden retriever on a park bench",
    "objects_detected": ["dog", "bench", "trees"],
    "scene_type": "outdoor",
    "confidence": "high"
  },
  "model_used": "gpt-4o-vision",
  "tool_used": null,
  "style_applied": "expert"
}
```

| Status | Code | Reason |
|--------|------|--------|
| 400 | UNSUPPORTED_FORMAT | File type not in accepted list |
| 400 | IMAGE_TOO_LARGE | Exceeds 10MB |
| 422 | PARSE_ERROR | Vision model output could not be parsed |
| 500 | VISION_MODEL_ERROR | Vision model call failed |

---

### GET /history

```
GET /api/v1/history?session_id=sess_abc123&user_id=u_001

// Response 200
{
  "session_id": "sess_abc123",
  "message_count": 4,
  "messages": [
    { "role": "human", "content": "What's the weather?", "timestamp": "2026-04-10T10:00:00Z" },
    { "role": "ai",    "content": "{\"temperature\": ...}", "timestamp": "2026-04-10T10:00:03Z" }
  ]
}
```

---

### DELETE /session

```json
// Request
{ "user_id": "u_001", "session_id": "sess_abc123" }

// Response 200
{ "message": "Session sess_abc123 cleared." }
```

---

### GET /user/{user_id}

```json
// Response 200
{
  "user_id": "u_001",
  "name": "Riya",
  "location": "Mumbai, India",
  "timezone": "Asia/Kolkata",
  "preferred_style": "expert"
}
```

---

### GET /health

```json
// Response 200
{ "status": "ok", "version": "1.0.0" }
```

---

## 7. Configuration

All config is read from `.env` via pydantic-settings in `core/config.py`. No `os.getenv` calls anywhere else.

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o and vision calls |
| `WEATHER_API_KEY` | OpenWeatherMap API key (leave blank to use mock data) |
| `USE_MOCK_WEATHER` | `true` / `false` — forces mock weather regardless of API key |
| `LOG_LEVEL` | `DEBUG` (dev) / `INFO` (prod) |
| `ENVIRONMENT` | `development` / `production` |
| `MAX_PARSER_RETRIES` | Max JSON parse retry attempts (default: `2`) |
| `MAX_AGENT_ITERATIONS` | Max ReAct loop iterations before forced stop (default: `5`) |

---

## 8. Error Handling

Global exception handlers are registered in `main.py`. Routes do not catch exceptions themselves — they raise domain exceptions which the global handler maps to HTTP responses.

All domain exceptions inherit from `AppException` in `core/exceptions.py`.

| Exception | Raised when | HTTP |
|-----------|-------------|------|
| `UserNotFound` | `user_id` not in profiles | 404 |
| `ParseError` | JSON parse failed after max retries | 422 |
| `UnsupportedImageFormat` | MIME type not in accepted list | 400 |
| `ImageTooLarge` | Upload exceeds 10MB | 400 |
| `ToolCallFailed` | Weather API error (after mock fallback attempted) | 502 |
| `AgentMaxIterations` | Agent exceeded `MAX_AGENT_ITERATIONS` | 500 |
| Unhandled | Any unexpected exception | 500 |

WeatherTool failures fall back to `mock_weather.json` before raising `ToolCallFailed`. The response includes `"data_source": "mock"` when fallback is used.

---

## 9. Logging

Structured JSON logging via structlog, configured in `core/logging.py`.

Every log entry includes:

| Field | Description |
|-------|-------------|
| `timestamp` | ISO 8601 |
| `level` | DEBUG / INFO / WARNING / ERROR |
| `message` | Human-readable description |
| `request_id` | UUID generated per request by middleware |
| `user_id` | From request context |
| `session_id` | From request context |
| `path` | API route |
| `status_code` | HTTP response code |
| `latency_ms` | Request duration |
| `tool_used` | Tool invoked by agent (if any) |
| `model_used` | LLM model name |
| `parser_retries` | Number of JSON parse retries (0, 1, or 2) |

**Never log:** API keys, image content, or raw LLM outputs that may contain user PII.

---

## 10. Testing

Test DB equivalent here is the memory store and mock profiles — tests use dependency overrides to inject these, not patching internals.

`conftest.py` provides: async test client, mock user profile, pre-seeded session memory, mock weather response.

**What to test (priority order):**

| Module | Scenarios |
|--------|-----------|
| Chat | Weather query → WeatherTool called, correct JSON returned |
| Chat | General query → no tool called, JSON returned |
| Chat | Unknown `user_id` → 404 |
| Chat | LLM returns bad JSON → retry triggered → valid JSON returned |
| Chat | LLM returns bad JSON × 3 → 422 |
| Image | Valid image → structured description returned |
| Image | Unsupported format → 400 |
| Image | Image over 10MB → 400 |
| Memory | Turn 2 response references Turn 1 context correctly |
| Memory | `DELETE /session` → subsequent request starts with empty history |
| Style | `style=child` → response uses child-friendly prompt prefix |
| Parser | Valid output → no retry |
| Parser | Invalid output → retry fires with corrective prompt |
| Tools | `WeatherTool` API failure → mock fallback used, `data_source: mock` in response |

Target: 75%+ coverage. Priority is agent routing, parser retry logic, and memory persistence over raw coverage number.

---

## 11. Developer Rules

### Code & Structure

- **One file, one responsibility** — `router.py` only routes. `agent.py` only builds and runs the agent. Never put business logic inside route handlers.
- **No `os.getenv` anywhere** — all config must go through `core/config.py`. If a new env var is needed, add it to the `Settings` class and `.env.example`.
- **No bare `except`** — always catch a specific exception. Bare `except` hides bugs silently.
- **No logic in `main.py`** — only router registration, middleware setup, and lifespan hooks.

### LangChain & Agent

- **Never call the LLM directly from a route** — all LLM calls go through the service layer (`chat_service.py`, `image_service.py`). Routes only call services.
- **Every new tool must have a mock** — any `@tool` function must support a mock mode controlled by an env var. No tool should make a live external call during tests.
- **Agent tools must be stateless** — tools must not read from or write to session memory. Memory is managed exclusively by the service layer.

### Prompts

- **No hardcoded strings in route or service files** — all prompt text lives in `app/prompts/`. If you're writing a string longer than one sentence near LLM code, it belongs in a prompt file.
- **Every prompt change must be tested** — if you change a prompt, add or update a test that verifies the LLM output still parses correctly against its schema.

### Output & Parsing

- **Never return raw LLM output to the client** — all responses go through the appropriate parser in `app/parsers/`. Raw text never leaves the service layer.
- **Parser retries are silent to the client** — the client always receives either a valid response or an error code. It never sees a retry message or raw parse error.

### API

- **All errors use the standard shape** — `{ "code": "...", "message": "..." }`. No custom error formats per endpoint.
- **Routes raise exceptions, never return error dicts** — raise an `AppException` subclass. The global handler in `main.py` converts it to the standard shape.

### Architecture & Components

- **Middleware handles fixed tasks only — never AI decisions** — Middleware is for input validation, logging, and profile loading. Any decision that involves reasoning or model selection belongs in the Router/Orchestrator. Never mix the two.
- **Only add a component when there is a confirmed need** — Don't add middleware, a new tool, or a new abstraction speculatively. If you're unsure whether something is needed, don't add it yet. Build the minimum that works, then extend when the need is proven.
- **Abstract critical components so they can be reused** — Memory management and routing logic must sit behind clean interfaces. Concrete implementations (in-memory store, keyword classifier) should be swappable without changing the components that depend on them.
- **Human in the Loop only at the single most critical pipeline step** — HITL adds two extra LLM calls per interaction and slows the pipeline. If it must be used, apply it at exactly one point where the cost of an autonomous mistake is highest. Never scatter it across multiple steps.
- **Flag unknown components in the design doc — research after implementation** — If you encounter a term or component you don't fully understand (e.g. `PydanticOutputParser`, `ConversationBufferMemory`), mark it clearly in the doc. Research it and add a clarifying comment in the code after you've built it. Don't block implementation on full upfront understanding.

---

## 12. How to Extend

**Add a new tool (e.g., News API):**
1. Create `app/tools/news_tool.py` with a `@tool`-decorated function
2. Import and add it to the tools list in `agent/agent.py`
3. Add a mock response in `data/mock_news.json` for tests

**Add a new response schema (e.g., for news):**
1. Create `app/parsers/news_parser.py` with a Pydantic model and `PydanticOutputParser`
2. The router will automatically use it if the agent selects the news tool
3. Do not change the response envelope shape — tool-specific data goes inside the `response` field. The top-level keys (`session_id`, `response`, `model_used`, `tool_used`, `style_applied`) must stay consistent for all downstream consumers

**Add a new communication style:**
1. Add the style name and its prompt prefix to `agent/style.py`
2. Update the `preferred_style` field validation in `request_models.py`

**Add a new API route:**
1. Create `app/api/routes/<name>.py`
2. Register it in `main.py` under the `/api/v1` prefix
