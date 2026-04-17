from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.budget_guard import BudgetGuard
from app.core.config_loader import ConfigLoader
from app.core.cost_tracker import CostRecord, CostTracker
from app.core.database import initialize_database


@pytest.mark.asyncio
async def test_cost_calculation_and_record(temp_db_path: str) -> None:
    loader = ConfigLoader("config", "prompts")
    runtime = loader.load()
    await initialize_database(temp_db_path)
    tracker = CostTracker(temp_db_path)
    model = runtime.models.models["gemini-flash-lite"]
    cost = tracker.calculate_cost(100, 50, model)
    assert cost > Decimal("0")
    await tracker.record(
        CostRecord(
            id=str(uuid4()),
            session_id=None,
            query_text="hello",
            category="faq",
            complexity="low",
            model_used="gemini-flash-lite",
            prompt_version="v1",
            classification_method="rule_based",
            prompt_tokens=100,
            completion_tokens=50,
            cost_usd=cost,
            budget_fallback_active=False,
            latency_ms=10,
        )
    )
    daily = await tracker.get_daily_spend()
    assert daily > Decimal("0")


@pytest.mark.asyncio
async def test_budget_enforcement(temp_db_path: str) -> None:
    loader = ConfigLoader("config", "prompts")
    runtime = loader.load()
    await initialize_database(temp_db_path)
    tracker = CostTracker(temp_db_path)
    guard = BudgetGuard(tracker, runtime.budget.budget)
    status = await guard.check_budget()
    assert status.budget_fallback_active is False
