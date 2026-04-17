from __future__ import annotations

import aiosqlite


REQUESTS_TABLE = """
CREATE TABLE IF NOT EXISTS requests (
    id TEXT PRIMARY KEY,
    session_id TEXT NULL,
    query_text TEXT NOT NULL,
    category TEXT NOT NULL,
    complexity TEXT NOT NULL,
    model_used TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    classification_method TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    cost_usd REAL NOT NULL,
    budget_fallback_active INTEGER NOT NULL,
    latency_ms INTEGER NULL,
    created_at TEXT NOT NULL
);
"""

CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS response_cache (
    cache_key TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    response_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NULL,
    hit_count INTEGER DEFAULT 0,
    last_accessed_at TEXT NOT NULL
);
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_requests_created_at ON requests(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_requests_category ON requests(category);",
    "CREATE INDEX IF NOT EXISTS idx_requests_model ON requests(model_used);",
    "CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON response_cache(expires_at);",
    "CREATE INDEX IF NOT EXISTS idx_cache_last_accessed ON response_cache(last_accessed_at);",
]


async def initialize_database(db_path: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute(REQUESTS_TABLE)
        await db.execute(CACHE_TABLE)
        for statement in INDEXES:
            await db.execute(statement)
        await db.commit()
