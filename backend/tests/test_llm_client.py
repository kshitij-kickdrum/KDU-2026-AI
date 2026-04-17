from __future__ import annotations

import json

import httpx
import pytest

from app.core.llm_client import LLMClient
from app.models.config import ModelDefinition


@pytest.mark.asyncio
async def test_openrouter_auth_header() -> None:
    captured = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("Authorization")
        payload = {
            "choices": [{"message": {"content": "ok"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 2},
        }
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    llm = LLMClient(
        models={
            "gpt-4o-mini": ModelDefinition(
                provider="openrouter",
                model_name="openai/gpt-4o-mini",
                input_cost_per_1k_tokens=0.1,
                output_cost_per_1k_tokens=0.2,
                max_tokens=10,
                timeout_seconds=10,
            )
        },
        openrouter_api_key="abc",
        client=client,
    )
    await llm.complete("gpt-4o-mini", "sys", "user")
    assert captured["auth"] == "Bearer abc"
    await client.aclose()


@pytest.mark.asyncio
async def test_retry_logic() -> None:
    attempts = {"n": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        if attempts["n"] < 4:
            return httpx.Response(500, text="fail")
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": "ok"}]}}],
                "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 1},
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    llm = LLMClient(
        models={
            "gemini-flash-lite": ModelDefinition(
                provider="gemini",
                model_name="gemini-2.0-flash-lite",
                input_cost_per_1k_tokens=0.1,
                output_cost_per_1k_tokens=0.2,
                max_tokens=10,
                timeout_seconds=10,
            )
        },
        gemini_api_key="k",
        client=client,
    )
    out = await llm.complete("gemini-flash-lite", "sys", "user")
    assert out.text == "ok"
    assert attempts["n"] == 4
    await client.aclose()
