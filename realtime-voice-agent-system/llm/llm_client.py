from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from collections.abc import AsyncIterator
from typing import Any

import httpx
from openai import AsyncOpenAI


@dataclass
class LLMResponse:
    content: str
    model_id: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    status: str
    error: str | None = None


class LLMClient:
    def __init__(
        self,
        openai_api_key: str | None,
        openrouter_api_key: str | None,
        openrouter_base_url: str = "https://openrouter.ai/api/v1",
        timeout_seconds: float = 10.0,
    ) -> None:
        self.openai_api_key = openai_api_key
        self.openrouter_api_key = openrouter_api_key
        self.timeout_seconds = timeout_seconds
        self._primary = AsyncOpenAI(api_key=openai_api_key) if openai_api_key else None
        self._fallback = (
            AsyncOpenAI(api_key=openrouter_api_key, base_url=openrouter_base_url)
            if openrouter_api_key
            else None
        )

    async def complete(
        self, messages: list[dict[str, str]], model: str = "gpt-4o-mini"
    ) -> LLMResponse:
        start = time.perf_counter()
        providers = [self._primary, self._fallback]
        last_error = None
        for client in providers:
            if client is None:
                continue
            try:
                response = await asyncio.wait_for(
                    self._call(client, messages, model), timeout=self.timeout_seconds
                )
                response.latency_ms = int((time.perf_counter() - start) * 1000)
                return response
            except Exception as exc:
                last_error = exc
                if _is_retryable(exc):
                    await asyncio.sleep(_retry_after(exc))
                    try:
                        response = await asyncio.wait_for(
                            self._call(client, messages, model),
                            timeout=self.timeout_seconds,
                        )
                        response.latency_ms = int((time.perf_counter() - start) * 1000)
                        return response
                    except Exception as retry_exc:
                        last_error = retry_exc
                        continue
        return LLMResponse(
            content="",
            model_id=model,
            prompt_tokens=0,
            completion_tokens=0,
            latency_ms=int((time.perf_counter() - start) * 1000),
            status="error",
            error=str(last_error or "no_llm_provider_configured"),
        )

    async def stream_complete(
        self, messages: list[dict[str, str]], model: str = "gpt-4o-mini"
    ) -> AsyncIterator[str]:
        providers = [self._primary, self._fallback]
        last_error: Exception | None = None
        for client in providers:
            if client is None:
                continue
            try:
                stream = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=model,
                        messages=messages,
                        stream=True,
                    ),
                    timeout=self.timeout_seconds,
                )
                async for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
                return
            except Exception as exc:
                last_error = exc
                if not _is_retryable(exc):
                    break
        raise RuntimeError(str(last_error or "no_llm_provider_configured"))

    async def _call(
        self, client: AsyncOpenAI, messages: list[dict[str, str]], model: str
    ) -> LLMResponse:
        response = await client.chat.completions.create(model=model, messages=messages)
        choice = response.choices[0].message.content or ""
        usage: Any = getattr(response, "usage", None)
        return LLMResponse(
            content=choice,
            model_id=model,
            prompt_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
            completion_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
            latency_ms=0,
            status="success",
        )


def _is_retryable(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    if status in (429, 500, 502, 503, 504):
        return True
    return isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, asyncio.TimeoutError))


def _retry_after(exc: Exception) -> float:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", {}) or {}
    try:
        return float(headers.get("retry-after", 5))
    except (TypeError, ValueError):
        return 5.0
