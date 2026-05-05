# Realtime Voice Agent System

Production-style local customer service system with voice input/output, agent handoffs, interruption handling, parallel worker agents, consensus aggregation, bounded concurrency, pruning, NDJSON monitoring, and session replay.

## Setup

```powershell
cd realtime-voice-agent-system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill `.env` with `OPENAI_API_KEY` and `OPENROUTER_API_KEY` for Phase 1 voice/transcription and live LLM calls. Phase 2 and Phase 3 can still demonstrate local orchestration with fallback responses when keys are absent.

## Environment

Key settings:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Primary OpenAI API key |
| `OPENROUTER_API_KEY` | Fallback OpenRouter API key |
| `LLM_MODEL` | Chat model, default `gpt-4o-mini` |
| `TRANSCRIPTION_MODEL` | Transcription model, default `gpt-4o-mini-transcribe` |
| `SQLITE_DB_PATH` | Local billing database path |
| `FAISS_INDEX_PATH` | Local FAISS index path |
| `FAISS_METADATA_PATH` | Vector metadata sidecar |
| `LOG_FILE_PATH` | NDJSON monitoring log path |
| `SQLITE_MAX_CONNECTIONS` | SQLite concurrency limit |
| `FAISS_MAX_CONNECTIONS` | FAISS concurrency limit |
| `QUEUE_TIMEOUT_SECONDS` | Resource queue timeout |

## Bootstrap Data

```powershell
python scripts/seed_db.py
python scripts/build_faiss_index.py
```

The FAISS builder writes a metadata fallback even if `faiss-cpu` is unavailable.

## Phase 1: Voice, Handoff, Interruption

```powershell
python main.py --phase 1 --text "What is my current billing balance for C-00123?"
python main.py --phase 1 --voice
python main.py --phase 1 --interactive --max-turns 5
```

Flow:

1. `TriageAgent` classifies the transcript.
2. It passes an `AgentState` snapshot containing `session_id`, `intent`, `transcript`, `message_history`, `timestamp_utc`, and `metadata`.
3. In interactive mode, `BillingAgent` streams LLM text, buffers complete sentences, and sends each sentence to TTS immediately.
4. `TTSEngine` uses Kokoro when available, otherwise prints/plays a generated fallback tone.
5. Interrupts use an `asyncio.Event`; playback checks the flag between short chunks and stops within the chunk boundary.

The audio layer contains direct `sounddevice` capture/playback adapters and VAD buffer logic. No prebuilt voice assistant wrapper is used. Use `--interactive` for the real barge-in demo: the microphone remains active in playback-monitoring mode while sentence-level TTS speaks, user speech raises the interrupt flag, playback stops, the active LLM stream is cancelled, the partial response is marked truncated, and the next utterance is captured as a fresh buffer.

## Phase 2: Parallel Execution and Consensus

```powershell
python main.py --phase 2 --query "What is the balance for C-00123?"
```

The `Coordinator` starts `DBAgent.query()` and `VectorAgent.search()` concurrently with `asyncio.create_task()` and aggregates with `ConsensusAgent`. If one worker fails, the successful result is preserved and the consensus response discloses the unavailable source. If both fail, the coordinator returns a structured error.

## Phase 3: 100-Session Simulation

```powershell
python main.py --phase 3
# or
python scripts/simulate_100_sessions.py
```

The simulation runs 100 concurrent sessions through the coordinator path and reports total time plus median latency.

## Concurrency Queue Design

Shared local resources are protected by `ConcurrencyQueue`, an `asyncio.Semaphore` wrapper:

```python
async with sqlite_queue.acquire():
    rows = await asyncio.to_thread(store.find_customer, lookup)
```

SQLite defaults to 5 simultaneous users and FAISS defaults to 10. If a request waits longer than `QUEUE_TIMEOUT_SECONDS`, the agent returns a structured timeout instead of blocking.

## Token Pruning Strategy

`AgentState` keeps at most 10 recent message turns. If the cumulative token count crosses 50,000, the oldest 5 turns are replaced by a compact summary message. System prompts are preserved during pruning, and pruning events are written to NDJSON logs.

## Monitoring and Replay

All significant events are logged as NDJSON:

```powershell
python scripts/replay_session.py <session_id>
```

Logs include LLM calls, tool invocations, handoffs with exact serialized `AgentState`, consensus events, pruning events, interrupt events, and coordinator errors. Exact JSON payloads make debugging reproducible because the handoff state can be replayed chronologically.

## Security

Secrets are loaded only from environment variables or `.env`. `.env` is listed in `.gitignore`, and startup warns if that protection is missing. The monitor redacts authorization headers and token-like keys before writing logs.
