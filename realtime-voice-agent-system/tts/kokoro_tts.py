from __future__ import annotations

import asyncio
import math
import time
from typing import Iterable

import numpy as np

from audio.playback import play_chunks
from monitoring.monitor import Monitor


class TTSEngine:
    def __init__(
        self,
        monitor: Monitor | None = None,
        sample_rate: int = 24000,
        chunk_ms: int = 50,
    ) -> None:
        self.monitor = monitor
        self.sample_rate = sample_rate
        self.chunk_ms = chunk_ms
        self._pipeline = None
        self._load_error: str | None = None

    def load(self) -> None:
        try:
            from kokoro import KPipeline

            self._pipeline = KPipeline(lang_code="a")
        except Exception as exc:
            self._load_error = str(exc)

    async def synthesize_and_play(
        self,
        text: str,
        interrupt_flag: asyncio.Event,
        session_id: str = "unknown",
    ) -> None:
        start = time.perf_counter()
        status = "success"
        try:
            if self._pipeline is None and self._load_error is None:
                self.load()
            chunks = self._synthesize(text)
            played = await play_chunks(chunks, self.sample_rate, interrupt_flag)
            if not played:
                print(text)
        except Exception as exc:
            status = "error"
            print(text)
            if self.monitor:
                await self.monitor.log(
                    {
                        "record_type": "tool_invocation",
                        "session_id": session_id,
                        "agent_name": "tts_engine",
                        "tool_name": "tts_synthesize",
                        "input_summary": text[:200],
                        "output_summary": str(exc)[:200],
                        "latency_ms": int((time.perf_counter() - start) * 1000),
                        "status": status,
                    }
                )
            return
        if self.monitor:
            await self.monitor.log(
                {
                    "record_type": "tool_invocation",
                    "session_id": session_id,
                    "agent_name": "tts_engine",
                    "tool_name": "tts_synthesize",
                    "input_summary": text[:200],
                    "output_summary": "played_or_console_fallback",
                    "latency_ms": int((time.perf_counter() - start) * 1000),
                    "status": status,
                }
            )

    def _synthesize(self, text: str) -> Iterable[np.ndarray]:
        if self._pipeline is not None:
            for _, _, audio in self._pipeline(text, voice="af_heart", speed=1.0):
                yield np.asarray(audio, dtype=np.float32)
            return
        duration = max(0.5, min(6.0, len(text.split()) * 0.18))
        total = int(self.sample_rate * duration)
        chunk = int(self.sample_rate * (self.chunk_ms / 1000))
        for start in range(0, total, chunk):
            size = min(chunk, total - start)
            t = np.arange(size, dtype=np.float32) / self.sample_rate
            yield (0.05 * np.sin(2 * math.pi * 220 * t)).astype(np.float32)

