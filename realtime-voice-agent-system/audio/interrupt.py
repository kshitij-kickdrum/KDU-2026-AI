from __future__ import annotations

import asyncio
from dataclasses import dataclass, field


@dataclass
class InterruptController:
    flag: asyncio.Event = field(default_factory=asyncio.Event)

    def trigger(self) -> None:
        self.flag.set()

    def clear(self) -> None:
        self.flag.clear()

    def is_interrupted(self) -> bool:
        return self.flag.is_set()


def flush_buffer(buffer: bytearray | list[bytes]) -> None:
    buffer.clear()

