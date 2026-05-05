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
) -> PlaybackStatus:
    try:
        import sounddevice as sd
    except Exception:
        return "fallback"

    for chunk in chunks:
        if interrupt_flag and interrupt_flag.is_set():
            sd.stop()
            return "interrupted"
        sd.play(chunk, samplerate=sample_rate, blocking=False)
        await asyncio.sleep(min(0.1, len(chunk) / sample_rate))
    if interrupt_flag and interrupt_flag.is_set():
        sd.stop()
        return "interrupted"
    sd.wait()
    return "completed"
