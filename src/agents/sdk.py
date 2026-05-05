from __future__ import annotations

from typing import Any

from src.core.exceptions import SDKUnavailableError


def load_agents_sdk() -> tuple[Any, Any, Any, Any]:
    try:
        from agents import Agent, ModelSettings, Runner, function_tool
    except ImportError as exc:
        raise SDKUnavailableError(
            "The OpenAI Agents SDK is required. Install dependencies with "
            "`pip install -r requirements.txt` and ensure `openai-agents` is available."
        ) from exc
    return Agent, Runner, function_tool, ModelSettings


def build_openrouter_model(model_name: str, api_key: str) -> Any:
    try:
        from agents import AsyncOpenAI, OpenAIChatCompletionsModel
    except ImportError as exc:
        raise SDKUnavailableError(
            "The OpenAI Agents SDK OpenAI-compatible model classes are required for OpenRouter."
        ) from exc
    return OpenAIChatCompletionsModel(
        model=model_name,
        openai_client=AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        ),
    )
