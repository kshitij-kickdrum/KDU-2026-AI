from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import aiosqlite

from app.core.llm_client import LLMClient
from app.models.config import ModelDefinition


@dataclass(slots=True)
class CostRecord:
    id: str
    session_id: str | None
    query_text: str
    category: str
    complexity: str
    model_used: str
    prompt_version: str
    classification_method: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: Decimal
    budget_fallback_active: bool
    latency_ms: int | None


class CostTracker:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    @staticmethod
    def calculate_cost(
        prompt_tokens: int, completion_tokens: int, model: ModelDefinition
    ) -> Decimal:
        return LLMClient.calculate_cost(prompt_tokens, completion_tokens, model)

    async def record(self, record: CostRecord) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO requests (
                    id, session_id, query_text, category, complexity, model_used,
                    prompt_version, classification_method, prompt_tokens,
                    completion_tokens, cost_usd, budget_fallback_active, latency_ms, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.session_id,
                    record.query_text,
                    record.category,
                    record.complexity,
                    record.model_used,
                    record.prompt_version,
                    record.classification_method,
                    record.prompt_tokens,
                    record.completion_tokens,
                    float(record.cost_usd),
                    int(record.budget_fallback_active),
                    record.latency_ms,
                    datetime.now(UTC).isoformat(),
                ),
            )
            await db.commit()

    async def _sum_cost(self, where_clause: str, params: tuple[Any, ...]) -> Decimal:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                f"SELECT COALESCE(SUM(cost_usd), 0) FROM requests WHERE {where_clause}", params
            ) as cursor:
                row = await cursor.fetchone()
        return Decimal(str(row[0] if row else 0))

    async def get_daily_spend(self, day_prefix: str | None = None) -> Decimal:
        if day_prefix is None:
            day_prefix = datetime.now(UTC).strftime("%Y-%m-%d")
        return await self._sum_cost("created_at LIKE ?", (f"{day_prefix}%",))

    async def get_monthly_spend(self, month_prefix: str | None = None) -> Decimal:
        if month_prefix is None:
            month_prefix = datetime.now(UTC).strftime("%Y-%m")
        return await self._sum_cost("created_at LIKE ?", (f"{month_prefix}%",))

    async def aggregate(self, period_prefix: str) -> dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT category, model_used, COUNT(*), COALESCE(SUM(cost_usd), 0)
                FROM requests
                WHERE created_at LIKE ?
                GROUP BY category, model_used
                """,
                (f"{period_prefix}%",),
            ) as cursor:
                rows = await cursor.fetchall()

            async with db.execute(
                "SELECT COUNT(*), COALESCE(SUM(cost_usd), 0) FROM requests WHERE created_at LIKE ?",
                (f"{period_prefix}%",),
            ) as cursor:
                summary = await cursor.fetchone()

        by_category: dict[str, dict[str, float | int]] = {}
        by_model: dict[str, dict[str, float | int]] = {}
        for category, model, count, cost in rows:
            category_bucket = by_category.setdefault(category, {"queries": 0, "cost_usd": 0.0})
            category_bucket["queries"] = int(category_bucket["queries"]) + int(count)
            category_bucket["cost_usd"] = float(category_bucket["cost_usd"]) + float(cost)

            model_bucket = by_model.setdefault(model, {"queries": 0, "cost_usd": 0.0})
            model_bucket["queries"] = int(model_bucket["queries"]) + int(count)
            model_bucket["cost_usd"] = float(model_bucket["cost_usd"]) + float(cost)

        return {
            "total_queries": int(summary[0] if summary else 0),
            "total_cost_usd": float(summary[1] if summary else 0.0),
            "by_category": by_category,
            "by_model": by_model,
        }
