from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import aiosqlite


@dataclass(slots=True)
class CacheStats:
    hits: int = 0
    misses: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total


class ResponseCache:
    TTL_BY_CATEGORY = {"faq": 3600, "booking": 900, "complaint": 0}

    def __init__(self, db_path: str, max_entries: int = 5000) -> None:
        self.db_path = db_path
        self.max_entries = max_entries
        self.stats = CacheStats()

    @staticmethod
    def normalize_query(query: str) -> str:
        return " ".join(query.lower().strip().split())

    @classmethod
    def cache_key(cls, query: str) -> str:
        normalized = cls.normalize_query(query)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    async def get(self, query: str) -> str | None:
        key = self.cache_key(query)
        now = datetime.now(UTC).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT response_text, expires_at
                FROM response_cache
                WHERE cache_key = ?
                """,
                (key,),
            ) as cursor:
                row = await cursor.fetchone()

            if not row:
                self.stats.misses += 1
                return None

            response_text, expires_at = row
            if expires_at and expires_at < now:
                await db.execute("DELETE FROM response_cache WHERE cache_key = ?", (key,))
                await db.commit()
                self.stats.misses += 1
                return None

            await db.execute(
                "UPDATE response_cache SET hit_count = hit_count + 1, last_accessed_at = ? WHERE cache_key = ?",
                (now, key),
            )
            await db.commit()
            self.stats.hits += 1
            return str(response_text)

    async def set(self, query: str, category: str, response_text: str) -> None:
        ttl = self.TTL_BY_CATEGORY.get(category, 0)
        if ttl <= 0:
            return
        key = self.cache_key(query)
        now = datetime.now(UTC)
        expires_at = (now + timedelta(seconds=ttl)).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO response_cache (
                    cache_key, category, response_text, created_at, expires_at, hit_count, last_accessed_at
                ) VALUES (?, ?, ?, ?, ?, COALESCE((SELECT hit_count FROM response_cache WHERE cache_key = ?), 0), ?)
                """,
                (
                    key,
                    category,
                    response_text,
                    now.isoformat(),
                    expires_at,
                    key,
                    now.isoformat(),
                ),
            )
            await self._evict_if_needed(db)
            await db.commit()

    async def _evict_if_needed(self, db: aiosqlite.Connection) -> None:
        async with db.execute("SELECT COUNT(*) FROM response_cache") as cursor:
            row = await cursor.fetchone()
        count = int(row[0] if row else 0)
        if count <= self.max_entries:
            return
        to_remove = count - self.max_entries
        await db.execute(
            """
            DELETE FROM response_cache
            WHERE cache_key IN (
                SELECT cache_key FROM response_cache
                ORDER BY last_accessed_at ASC
                LIMIT ?
            )
            """,
            (to_remove,),
        )

    async def total_entries(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM response_cache") as cursor:
                row = await cursor.fetchone()
        return int(row[0] if row else 0)
