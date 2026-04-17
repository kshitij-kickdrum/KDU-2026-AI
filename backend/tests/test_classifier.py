from __future__ import annotations

import pytest

from app.core.classifier import HybridClassifier
from app.core.llm_client import LLMClient
from app.core.prompt_manager import PromptManager


class StubLLM(LLMClient):
    def __init__(self) -> None:
        pass

    async def classify_with_gemini(self, model_key: str, prompt: str, query: str) -> dict:
        return {"category": "booking", "complexity": "medium"}


@pytest.mark.asyncio
async def test_rule_based_classification(config_loader) -> None:
    runtime = config_loader.load()
    classifier = HybridClassifier(
        llm_client=StubLLM(),
        prompt_manager=PromptManager(config_loader, prompts_dir="prompts"),
        features=runtime.settings.features,
    )
    result = await classifier.classify("I need to schedule an appointment tomorrow")
    assert result.category == "booking"
    assert result.method == "rule_based"


@pytest.mark.asyncio
async def test_llm_fallback_path(config_loader) -> None:
    runtime = config_loader.load()
    classifier = HybridClassifier(
        llm_client=StubLLM(),
        prompt_manager=PromptManager(config_loader, prompts_dir="prompts"),
        features=runtime.settings.features,
    )
    result = await classifier.classify("hello")
    assert result.method in {"rule_based", "llm_fallback"}
