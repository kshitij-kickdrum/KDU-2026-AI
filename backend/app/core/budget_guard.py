from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal

from app.core.cost_tracker import CostTracker
from app.models.config import BudgetPolicy


@dataclass(slots=True)
class BudgetStatus:
    daily_remaining_usd: Decimal
    monthly_remaining_usd: Decimal
    budget_fallback_active: bool


class BudgetGuard:
    def __init__(self, cost_tracker: CostTracker, policy: BudgetPolicy) -> None:
        self.cost_tracker = cost_tracker
        self.policy = policy
        self._warned_daily = False
        self._warned_monthly = False
        self.logger = logging.getLogger(__name__)

    async def check_budget(self) -> BudgetStatus:
        daily_spend = await self.cost_tracker.get_daily_spend()
        monthly_spend = await self.cost_tracker.get_monthly_spend()

        daily_remaining = self.policy.daily_limit_usd - daily_spend
        monthly_remaining = self.policy.monthly_limit_usd - monthly_spend

        daily_ratio = (
            daily_spend / self.policy.daily_limit_usd
            if self.policy.daily_limit_usd
            else Decimal("0")
        )
        monthly_ratio = (
            monthly_spend / self.policy.monthly_limit_usd
            if self.policy.monthly_limit_usd
            else Decimal("0")
        )
        threshold = self.policy.warning_threshold_ratio

        if daily_ratio >= threshold and not self._warned_daily:
            self.logger.warning("Daily budget threshold reached")
            self._warned_daily = True
        if monthly_ratio >= threshold and not self._warned_monthly:
            self.logger.warning("Monthly budget threshold reached")
            self._warned_monthly = True

        fallback_active = daily_remaining <= 0 or monthly_remaining <= 0
        return BudgetStatus(
            daily_remaining_usd=max(Decimal("0"), daily_remaining),
            monthly_remaining_usd=max(Decimal("0"), monthly_remaining),
            budget_fallback_active=fallback_active,
        )
