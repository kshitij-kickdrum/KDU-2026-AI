from __future__ import annotations

from app.models.config import RoutingConfig


class QueryRouter:
    def __init__(self, routing_config: RoutingConfig) -> None:
        self.routing_config = routing_config

    def route(self, category: str, complexity: str, budget_fallback_active: bool) -> str:
        if budget_fallback_active:
            return self.routing_config.fallback["cheapest_model"]
        return self.routing_config.routing[category][complexity]
