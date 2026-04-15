from __future__ import annotations

from cachetools import TTLCache


class CacheManager:
    def __init__(self) -> None:
        self.embedding_cache: dict[str, list[float]] = {}
        self.query_cache: TTLCache[str, object] = TTLCache(maxsize=1000, ttl=3600)

    def get_embedding(self, key: str) -> list[float] | None:
        return self.embedding_cache.get(key)

    def set_embedding(self, key: str, value: list[float]) -> None:
        self.embedding_cache[key] = value

    def get_query(self, key: str) -> object | None:
        return self.query_cache.get(key)

    def set_query(self, key: str, value: object) -> None:
        self.query_cache[key] = value

