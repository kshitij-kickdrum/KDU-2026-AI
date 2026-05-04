from __future__ import annotations

import asyncio
from typing import Iterable

import numpy as np


async def play_chunks(
    chunks: Iterable[np.ndarray],
    sample_rate: int,
    interrupt_flag: asyncio.Event | None = None,
) -> bool:
    try:
        import sounddevice as sd
    except Exception:
        return False

    for chunk in chunks:
        if interrupt_flag and interrupt_flag.is_set():
            sd.stop()
            return False
        sd.play(chunk, samplerate=sample_rate, blocking=False)
        await asyncio.sleep(min(0.1, len(chunk) / sample_rate))
    sd.wait()
    return True

