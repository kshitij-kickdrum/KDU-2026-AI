from __future__ import annotations

import pytest

from app.core.cache import ResponseCache
from app.core.database import initialize_database


@pytest.mark.asyncio
async def test_cache_hit_and_stats(temp_db_path: str) -> None:
    await initialize_database(temp_db_path)
    cache = ResponseCache(temp_db_path, max_entries=2)
    await cache.set("  Hello   World ", "faq", "response1")
    hit = await cache.get("hello world")
    assert hit == "response1"
    assert cache.stats.hits == 1
    assert cache.stats.hit_rate == 1.0


@pytest.mark.asyncio
async def test_cache_lru_eviction(temp_db_path: str) -> None:
    await initialize_database(temp_db_path)
    cache = ResponseCache(temp_db_path, max_entries=2)
    await cache.set("q1", "faq", "r1")
    await cache.set("q2", "faq", "r2")
    _ = await cache.get("q1")
    await cache.set("q3", "faq", "r3")
    assert await cache.get("q2") is None
