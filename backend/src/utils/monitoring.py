from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager


class Metrics:
    def __init__(self) -> None:
        self.counters: dict[str, int] = defaultdict(int)
        self.timings_ms: dict[str, list[float]] = defaultdict(list)

    def incr(self, key: str, amount: int = 1) -> None:
        self.counters[key] += amount

    def timing(self, key: str, elapsed_ms: float) -> None:
        self.timings_ms[key].append(elapsed_ms)

    @contextmanager
    def track(self, key: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            self.timing(key, (time.perf_counter() - start) * 1000.0)

    def summary(self) -> dict:
        avg = {k: (sum(v) / len(v) if v else 0.0) for k, v in self.timings_ms.items()}
        return {"counters": dict(self.counters), "timings_avg_ms": avg}


GLOBAL_METRICS = Metrics()

