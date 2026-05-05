from __future__ import annotations

import asyncio
import time
from uuid import uuid4

from agents.billing_agent import BillingAgent
from agents.triage_agent import TriageAgent
from audio.capture import AudioPipeline
from audio.interrupt import InterruptController
from config.settings import Settings
from monitoring.monitor import Monitor
from state.agent_state import AgentState
from transcription.transcriber import Transcriber
from tts.kokoro_tts import TTSEngine


class VoiceSession:
    def __init__(
        self,
        settings: Settings,
        monitor: Monitor,
        triage_agent: TriageAgent,
        billing_agent: BillingAgent,
        tts_engine: TTSEngine,
        max_turns: int = 5,
    ) -> None:
        self.settings = settings
        self.monitor = monitor
        self.triage_agent = triage_agent
        self.billing_agent = billing_agent
        self.tts_engine = tts_engine
        self.max_turns = max_turns
        self.session_id = str(uuid4())
        self.interrupt = InterruptController()
        self.pipeline = AudioPipeline(
            settings.audio_sample_rate,
            settings.audio_silence_threshold,
            settings.audio_speech_min_duration_ms,
            settings.audio_silence_min_duration_ms,
            self.interrupt,
        )
        self.transcriber = Transcriber(
            settings.openai_api_key,
            settings.transcription_model,
            monitor,
            sample_rate=settings.audio_sample_rate,
        )
        self._utterances: asyncio.Queue[bytes] = asyncio.Queue()
        self._state: AgentState | None = None

    async def run(self) -> str:
        await self.monitor.log(
            {
                "record_type": "session_start",
                "session_id": self.session_id,
                "status": "active",
                "total_turns": 0,
                "total_latency_ms": 0,
            }
        )
        self.pipeline.on_speech_detected(self._on_speech)
        print("Interactive voice mode is listening. Press Ctrl+C to stop.")
        self.pipeline.start_capture()
        turns = 0
        started = time.perf_counter()
        try:
            while turns < self.max_turns:
                print("Speak now, then pause...")
                audio_bytes = await self._utterances.get()
                transcript = await self.transcriber.transcribe(
                    audio_bytes, self.session_id
                )
                if not transcript:
                    print("No transcript returned; listening again.")
                    continue
                print(f"user: {transcript}")
                await self._handle_transcript(transcript)
                turns += 1
        finally:
            self.pipeline.stop_capture()
            await self.monitor.log(
                {
                    "record_type": "session_end",
                    "session_id": self.session_id,
                    "status": "completed",
                    "total_turns": turns,
                    "total_latency_ms": int((time.perf_counter() - started) * 1000),
                }
            )
        return self.session_id

    async def _on_speech(self, audio_bytes: bytes) -> None:
        await self._utterances.put(audio_bytes)

    async def _handle_transcript(self, transcript: str) -> None:
        base_state = self._state or AgentState(
            self.session_id, "general_inquiry", transcript, []
        )
        base_state.transcript = transcript
        self._state = await self.triage_agent.classify(transcript, base_state)
        response = await self.billing_agent.respond(self._state)
        print(f"assistant: {response}")

        self.interrupt.clear()
        self.pipeline.set_playing(True)
        try:
            interrupted = await self.tts_engine.synthesize_and_play(
                response,
                self.interrupt.flag,
                self.session_id,
            )
        finally:
            self.pipeline.set_playing(False)

        if interrupted or self.interrupt.is_interrupted():
            self.billing_agent.mark_truncated(self._state, response)
            await self.monitor.log(
                {
                    "record_type": "interrupt_event",
                    "session_id": self.session_id,
                    "truncated_response_length": len(response),
                    "interrupt_source": "user_speech",
                }
            )
            print("Interrupted. Listening for your new utterance...")
            self.interrupt.clear()
