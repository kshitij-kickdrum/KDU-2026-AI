from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from app.core.budget_guard import BudgetGuard
from app.core.cache import ResponseCache
from app.core.classifier import HybridClassifier
from app.core.config_loader import ConfigLoader
from app.core.cost_tracker import CostTracker
from app.core.llm_client import LLMClient
from app.core.prompt_manager import PromptManager
from app.core.router import QueryRouter
from app.core.summarizer import QuerySummarizer


@dataclass(slots=True)
class Services:
    config_loader: ConfigLoader
    prompt_manager: PromptManager
    llm_client: LLMClient
    classifier: HybridClassifier
    router: QueryRouter
    cache: ResponseCache
    summarizer: QuerySummarizer
    cost_tracker: CostTracker
    budget_guard: BudgetGuard


def get_services(request: Request) -> Services:
    return request.app.state.services
