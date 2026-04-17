from __future__ import annotations

import os
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from dotenv import load_dotenv

from app.api.dependencies import Services
from app.api.routes import admin, health, query
from app.core.budget_guard import BudgetGuard
from app.core.cache import ResponseCache
from app.core.classifier import HybridClassifier
from app.core.config_loader import ConfigLoader
from app.core.cost_tracker import CostTracker
from app.core.database import initialize_database
from app.core.llm_client import LLMClient
from app.core.prompt_manager import PromptManager
from app.core.router import QueryRouter
from app.core.summarizer import QuerySummarizer
from app.utils.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    config_loader = ConfigLoader(config_dir="config", prompts_dir="prompts")
    runtime = config_loader.load()
    configure_logging(runtime.settings.app.log_level)
    Path("data").mkdir(parents=True, exist_ok=True)
    await initialize_database(runtime.settings.app.database_path)

    prompt_manager = PromptManager(config_loader=config_loader, prompts_dir="prompts")
    llm_client = LLMClient(
        models=runtime.models.models,
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
    )
    cost_tracker = CostTracker(runtime.settings.app.database_path)
    budget_guard = BudgetGuard(cost_tracker=cost_tracker, policy=runtime.budget.budget)
    services = Services(
        config_loader=config_loader,
        prompt_manager=prompt_manager,
        llm_client=llm_client,
        classifier=HybridClassifier(
            llm_client=llm_client,
            prompt_manager=prompt_manager,
            features=runtime.settings.features,
            llm_fallback_model="gpt-4o-mini",
        ),
        router=QueryRouter(runtime.routing),
        cache=ResponseCache(runtime.settings.app.database_path),
        summarizer=QuerySummarizer(llm_client=llm_client, model_key="gpt-4o-mini"),
        cost_tracker=cost_tracker,
        budget_guard=budget_guard,
    )
    app.state.services = services
    app.state.rate_limits = defaultdict(deque)
    yield
    await llm_client.client.aclose()


def create_app() -> FastAPI:
    app = FastAPI(title="FixIt AI Support System", lifespan=lifespan)
    app.include_router(query.router)
    app.include_router(admin.router)
    app.include_router(health.router)
    return app


app = create_app()
