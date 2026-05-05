from __future__ import annotations

import asyncio
import io
import time
import wave

from openai import AsyncOpenAI

from monitoring.monitor import Monitor


class Transcriber:
    def __init__(
        self,
        api_key: str | None,
        model: str = "gpt-4o-mini-transcribe",
        monitor: Monitor | None = None,
        timeout_seconds: float = 3.0,
        sample_rate: int = 16000,
    ) -> None:
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None
        self.model = model
        self.monitor = monitor
        self.timeout_seconds = timeout_seconds
        self.sample_rate = sample_rate

    async def transcribe(self, audio_bytes: bytes, session_id: str = "unknown") -> str:
        if self.client is None:
            return ""
        start = time.perf_counter()
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                result = await asyncio.wait_for(
                    self._request(audio_bytes), timeout=self.timeout_seconds
                )
                await self._log(session_id, "success", start)
                return result
            except Exception as exc:
                last_error = exc
                if attempt == 0:
                    await asyncio.sleep(1)
        await self._log(session_id, "error", start, str(last_error))
        return ""

    async def _request(self, audio_bytes: bytes) -> str:
        wav = _pcm_to_wav(audio_bytes, self.sample_rate)
        wav.name = "speech.wav"
        response = await self.client.audio.transcriptions.create(
            model=self.model,
            file=wav,
        )
        return str(getattr(response, "text", ""))

    async def _log(
        self, session_id: str, status: str, start: float, error: str | None = None
    ) -> None:
        if self.monitor:
            await self.monitor.log(
                {
                    "record_type": "llm_call",
                    "session_id": session_id,
                    "agent_name": "transcriber",
                    "model_id": self.model,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "latency_ms": int((time.perf_counter() - start) * 1000),
                    "status": status,
                    "error": error,
                }
            )


def _pcm_to_wav(audio_bytes: bytes, sample_rate: int) -> io.BytesIO:
    handle = io.BytesIO()
    with wave.open(handle, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(audio_bytes)
    handle.seek(0)
    return handle

