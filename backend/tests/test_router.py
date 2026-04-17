from __future__ import annotations

from app.core.config_loader import ConfigLoader
from app.core.router import QueryRouter


def test_router_budget_fallback() -> None:
    loader = ConfigLoader("config", "prompts")
    runtime = loader.load()
    router = QueryRouter(runtime.routing)
    model = router.route("faq", "high", budget_fallback_active=True)
    assert model == "gemini-flash-lite"


def test_property_routing_consistency() -> None:
    loader = ConfigLoader("config", "prompts")
    runtime = loader.load()
    router = QueryRouter(runtime.routing)
    for category in ["faq", "complaint", "booking"]:
        for complexity in ["low", "medium", "high"]:
            a = router.route(category, complexity, budget_fallback_active=False)
            b = router.route(category, complexity, budget_fallback_active=False)
            assert a == b
