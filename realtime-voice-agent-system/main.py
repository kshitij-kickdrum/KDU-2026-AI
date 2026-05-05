from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path
from uuid import uuid4

from agents.billing_agent import BillingAgent
from agents.consensus_agent import ConsensusAgent
from agents.coordinator import Coordinator
from agents.db_agent import DBAgent
from agents.triage_agent import TriageAgent
from agents.vector_agent import VectorAgent
from audio.capture import AudioPipeline
from audio.interrupt import InterruptController
from concurrency.queue_manager import ConcurrencyQueue
from config.settings import ConfigurationError, Settings
from core.voice_session import VoiceSession
from llm.llm_client import LLMClient
from monitoring.monitor import Monitor
from state.agent_state import AgentState
from storage.faiss_store import FAISSStore
from storage.sqlite_store import SQLiteStore
from transcription.transcriber import Transcriber
from tts.kokoro_tts import TTSEngine


async def run_phase1(
    settings: Settings,
    text: str | None,
    voice: bool = False,
    interrupt_demo: bool = False,
    interactive: bool = False,
    max_turns: int = 5,
) -> None:
    monitor = Monitor(settings.log_file_path)
    llm = LLMClient(settings.openai_api_key, settings.openrouter_api_key, settings.openrouter_base_url)
    tts = TTSEngine(monitor)
    triage = TriageAgent(llm, monitor, settings.llm_model)
    billing = BillingAgent(llm, monitor, settings.llm_model, tts_engine=tts)
    if interactive:
        session = VoiceSession(settings, monitor, triage, billing, tts, max_turns)
        session_id = await session.run()
        print(f"session_id={session_id}")
        return

    interrupt = InterruptController()
    session_id = str(uuid4())
    await monitor.log({"record_type": "session_start", "session_id": session_id, "status": "active", "total_turns": 0, "total_latency_ms": 0})
    if voice:
        transcript = await capture_and_transcribe(settings, monitor, session_id, interrupt)
    else:
        transcript = text or input("Speak/type a billing question for Phase 1 demo: ").strip()
    state = AgentState(session_id, "general_inquiry", transcript, [])
    state = await triage.classify(transcript, state)
    response = await billing.respond(state)
    if interrupt_demo:
        await run_interrupt_demo(tts, billing, state, interrupt, monitor, response)
    else:
        await tts.synthesize_and_play(response, interrupt.flag, session_id)
    await monitor.log({"record_type": "session_end", "session_id": session_id, "status": "completed", "total_turns": 1, "total_latency_ms": 0})
    print(f"session_id={session_id}")
    print(response)


async def run_interrupt_demo(
    tts: TTSEngine,
    billing: BillingAgent,
    state: AgentState,
    interrupt: InterruptController,
    monitor: Monitor,
    response: str,
) -> None:
    long_response = (
        response
        + " "
        + "This extra spoken content is included to make the interruption demo long enough "
        "to stop playback before the response finishes. " * 8
    )

    async def trigger_interrupt() -> None:
        await asyncio.sleep(0.5)
        interrupt.trigger()

    trigger_task = asyncio.create_task(trigger_interrupt())
    await tts.synthesize_and_play(long_response, interrupt.flag, state.session_id)
    await trigger_task
    unspoken_text = long_response[int(len(long_response) * 0.5) :]
    billing.mark_truncated(state, unspoken_text)
    await monitor.log(
        {
            "record_type": "interrupt_event",
            "session_id": state.session_id,
            "truncated_response_length": len(unspoken_text),
            "interrupt_source": "user_speech",
        }
    )
    print("interrupt_demo=triggered")


async def run_phase2(settings: Settings, query: str) -> None:
    monitor = Monitor(settings.log_file_path)
    llm = LLMClient(settings.openai_api_key, settings.openrouter_api_key, settings.openrouter_base_url)
    coordinator = _build_coordinator(settings, monitor, llm)
    session_id = str(uuid4())
    result = await coordinator.run(query, session_id)
    print(f"session_id={session_id}")
    print(f"db={result.db_agent_status} vector={result.vector_agent_status}")
    print(result.response)


async def run_phase3(settings: Settings) -> None:
    script = Path(__file__).parent / "scripts" / "simulate_100_sessions.py"
    process = await asyncio.create_subprocess_exec(sys.executable, str(script))
    await process.wait()
    if process.returncode:
        raise SystemExit(process.returncode)


def _build_coordinator(settings: Settings, monitor: Monitor, llm: LLMClient) -> Coordinator:
    sqlite_queue = ConcurrencyQueue(settings.sqlite_max_connections, settings.queue_timeout_seconds)
    faiss_queue = ConcurrencyQueue(settings.faiss_max_connections, settings.queue_timeout_seconds)
    return Coordinator(
        DBAgent(SQLiteStore(settings.sqlite_db_path), sqlite_queue, monitor),
        VectorAgent(FAISSStore(settings.faiss_index_path, settings.faiss_metadata_path), faiss_queue, monitor),
        ConsensusAgent(llm, monitor, settings.llm_model),
        monitor,
    )


async def transcribe_once(settings: Settings, audio_path: str) -> None:
    monitor = Monitor(settings.log_file_path)
    transcriber = Transcriber(settings.openai_api_key, settings.transcription_model, monitor, sample_rate=settings.audio_sample_rate)
    audio_bytes = Path(audio_path).read_bytes()
    started = time.perf_counter()
    text = await transcriber.transcribe(audio_bytes, str(uuid4()))
    print(f"latency_ms={int((time.perf_counter() - started) * 1000)}")
    print(text)


async def capture_and_transcribe(
    settings: Settings,
    monitor: Monitor,
    session_id: str,
    interrupt: InterruptController,
) -> str:
    loop = asyncio.get_running_loop()
    utterance: asyncio.Future[bytes] = loop.create_future()
    pipeline = AudioPipeline(
        settings.audio_sample_rate,
        settings.audio_silence_threshold,
        settings.audio_speech_min_duration_ms,
        settings.audio_silence_min_duration_ms,
        interrupt,
    )

    async def on_speech(audio_bytes: bytes) -> None:
        if not utterance.done():
            utterance.set_result(audio_bytes)

    pipeline.on_speech_detected(on_speech)
    print("Listening. Speak once, then pause for silence detection...")
    pipeline.start_capture()
    try:
        audio_bytes = await utterance
    finally:
        pipeline.stop_capture()
    transcriber = Transcriber(
        settings.openai_api_key,
        settings.transcription_model,
        monitor,
        sample_rate=settings.audio_sample_rate,
    )
    transcript = await transcriber.transcribe(audio_bytes, session_id)
    if not transcript:
        raise RuntimeError("Transcription returned no text.")
    return transcript


async def main_async() -> None:
    parser = argparse.ArgumentParser(description="Realtime voice agent system")
    parser.add_argument("--phase", choices=["1", "2", "3"], default="1")
    parser.add_argument("--query", default="What is the balance for C-00123?")
    parser.add_argument("--text", help="Typed transcript for Phase 1 demo")
    parser.add_argument("--voice", action="store_true", help="Use microphone capture for Phase 1")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run continuous Phase 1 voice loop with live barge-in interruption",
    )
    parser.add_argument("--max-turns", type=int, default=5)
    parser.add_argument(
        "--interrupt-demo",
        action="store_true",
        help="Trigger a deterministic playback interruption during Phase 1",
    )
    parser.add_argument("--transcribe-audio", help="Raw 16-bit PCM audio file to transcribe")
    args = parser.parse_args()
    require_keys = args.phase == "1" or bool(args.transcribe_audio)
    settings = Settings.load(require_api_keys=require_keys)
    if args.transcribe_audio:
        await transcribe_once(settings, args.transcribe_audio)
    elif args.phase == "1":
        await run_phase1(
            settings,
            args.text,
            args.voice,
            args.interrupt_demo,
            args.interactive,
            args.max_turns,
        )
    elif args.phase == "2":
        await run_phase2(settings, args.query)
    else:
        await run_phase3(settings)


def main() -> None:
    try:
        asyncio.run(main_async())
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
