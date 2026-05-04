from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import numpy as np

from audio.interrupt import InterruptController


class AudioPipeline:
    def __init__(
        self,
        sample_rate: int = 16000,
        silence_threshold: float = 500.0,
        speech_min_duration_ms: int = 300,
        silence_min_duration_ms: int = 700,
        interrupt_controller: InterruptController | None = None,
    ) -> None:
        self.sample_rate = sample_rate
        self.silence_threshold = silence_threshold
        self.speech_min_duration_ms = speech_min_duration_ms
        self.silence_min_duration_ms = silence_min_duration_ms
        self.interrupt_controller = interrupt_controller or InterruptController()
        self._callback: Callable[[bytes], Awaitable[None]] | None = None
        self._buffer = bytearray()
        self._is_buffering = False
        self._speech_ms = 0.0
        self._silence_ms = 0.0
        self._stream: Any | None = None
        self._is_playing = False
        self._loop: asyncio.AbstractEventLoop | None = None

    def on_speech_detected(self, callback: Callable[[bytes], Awaitable[None]]) -> None:
        self._callback = callback

    def start_capture(self) -> None:
        try:
            import sounddevice as sd

            self._loop = asyncio.get_running_loop()
            self._stream = sd.InputStream(
                channels=1,
                samplerate=self.sample_rate,
                dtype="int16",
                callback=self._audio_callback,
            )
            self._stream.start()
        except Exception as exc:
            raise RuntimeError(f"Unable to start microphone capture: {exc}") from exc

    def stop_capture(self) -> None:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def set_playing(self, is_playing: bool) -> None:
        self._is_playing = is_playing

    def process_frame(self, frame: bytes, duration_ms: float) -> bytes | None:
        energy = self._energy(frame)
        speech = energy > self.silence_threshold
        if self._is_playing and speech:
            self.interrupt_controller.trigger()
            self._buffer.clear()
            self._is_buffering = False
            self._speech_ms = 0.0
            self._silence_ms = 0.0
            return None

        if speech:
            self._speech_ms += duration_ms
            self._silence_ms = 0.0
            if self._speech_ms >= self.speech_min_duration_ms:
                self._is_buffering = True
            if self._is_buffering:
                self._buffer.extend(frame)
            return None

        if self._is_buffering:
            self._silence_ms += duration_ms
            self._buffer.extend(frame)
            if self._silence_ms >= self.silence_min_duration_ms:
                finalized = bytes(self._buffer)
                self._buffer.clear()
                self._is_buffering = False
                self._speech_ms = 0.0
                self._silence_ms = 0.0
                return finalized
        else:
            self._speech_ms = 0.0
        return None

    def _audio_callback(self, indata: Any, frames: int, time_info: Any, status: Any) -> None:
        frame = bytes(indata)
        duration_ms = (frames / self.sample_rate) * 1000
        finalized = self.process_frame(frame, duration_ms)
        if finalized and self._callback and self._loop:
            asyncio.run_coroutine_threadsafe(self._callback(finalized), self._loop)

    @staticmethod
    def _energy(frame: bytes) -> float:
        if not frame:
            return 0.0
        samples = np.frombuffer(frame, dtype=np.int16)
        if samples.size == 0:
            return 0.0
        return float(np.sqrt(np.mean(np.square(samples.astype(np.float64)))))
