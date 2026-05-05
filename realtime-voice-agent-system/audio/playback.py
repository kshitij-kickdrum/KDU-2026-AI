from __future__ import annotations

import asyncio
from typing import Literal
from typing import Iterable

import numpy as np

PlaybackStatus = Literal["completed", "interrupted", "fallback"]


async def play_chunks(
    chunks: Iterable[np.ndarray],
    sample_rate: int,
    interrupt_flag: asyncio.Event | None = None,
    max_chunk_ms: int = 50,
) -> PlaybackStatus:
    try:
        import sounddevice as sd
    except Exception:
        return "fallback"

    max_frames = max(1, int(sample_rate * (max_chunk_ms / 1000)))
    for chunk in chunks:
        audio = np.asarray(chunk, dtype=np.float32).reshape(-1)
        for start in range(0, len(audio), max_frames):
            if interrupt_flag and interrupt_flag.is_set():
                sd.stop()
                return "interrupted"
            piece = audio[start : start + max_frames]
            sd.play(piece, samplerate=sample_rate, blocking=False)
            await asyncio.sleep(len(piece) / sample_rate)
    if interrupt_flag and interrupt_flag.is_set():
        sd.stop()
        return "interrupted"
    return "completed"
