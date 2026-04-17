from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import httpx

from app.models.config import ModelDefinition


class LLMServiceUnavailable(RuntimeError):
    pass


class LLMProviderError(RuntimeError):
    def __init__(self, provider: str, status_code: int | None, detail: str) -> None:
        self.provider = provider
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"{provider} failed (status={status_code}): {detail}")


@dataclass(slots=True)
class LLMResponse:
    text: str
    prompt_tokens: int
    completion_tokens: int


class LLMClient:
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
    logger = logging.getLogger(__name__)

    def __init__(
        self,
        models: dict[str, ModelDefinition],
        openrouter_api_key: str = "",
        gemini_api_key: str = "",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.models = models
        self.openrouter_api_key = openrouter_api_key
        self.gemini_api_key = gemini_api_key
        self.client = client or httpx.AsyncClient(timeout=30)

    async def _with_retry(self, fn: Any) -> Any:
        delays = [0, 1, 2, 4]
        last_err: Exception | None = None
        for attempt, delay in enumerate(delays):
            if delay:
                await asyncio.sleep(delay)
            try:
                return await fn()
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                self.logger.warning(
                    "LLM attempt failed",
                    extra={
                        "context": {
                            "attempt": attempt + 1,
                            "max_attempts": len(delays),
                            "error": str(exc),
                        }
                    },
                )
                if attempt == len(delays) - 1:
                    break
        message = f"All providers failed after retries: {last_err}"
        raise LLMServiceUnavailable(message) from last_err

    async def complete(self, model_key: str, prompt: str, query: str) -> LLMResponse:
        model = self.models[model_key]
        if model.provider == "openrouter":
            return await self._with_retry(
                lambda: self._complete_openrouter(model, prompt, query)
            )
        return await self._with_retry(lambda: self._complete_gemini(model, prompt, query))

    async def classify_with_gemini(self, model_key: str, prompt: str, query: str) -> dict:
        response = await self.complete(model_key=model_key, prompt=prompt, query=query)
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {"category": "faq", "complexity": "medium"}

    async def summarize_with_gemini(self, model_key: str, text: str) -> str:
        result = await self.complete(
            model_key=model_key,
            prompt="Summarize in <= 40 words preserving key support details.",
            query=text,
        )
        return result.text

    async def _complete_openrouter(
        self, model: ModelDefinition, prompt: str, query: str
    ) -> LLMResponse:
        if not self.openrouter_api_key:
            raise LLMProviderError(
                provider="openrouter",
                status_code=None,
                detail="OPENROUTER_API_KEY is missing",
            )
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model.model_name,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": query},
            ],
            "max_tokens": model.max_tokens,
        }
        r = await self.client.post(self.OPENROUTER_URL, headers=headers, json=payload)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            raise LLMProviderError(
                provider="openrouter",
                status_code=exc.response.status_code,
                detail=detail,
            ) from exc
        body = r.json()
        usage = body.get("usage", {})
        text = body["choices"][0]["message"]["content"]
        return LLMResponse(
            text=text,
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
        )

    async def _complete_gemini(self, model: ModelDefinition, prompt: str, query: str) -> LLMResponse:
        if not self.gemini_api_key:
            raise LLMProviderError(
                provider="gemini",
                status_code=None,
                detail="GEMINI_API_KEY is missing",
            )
        url = f"{self.GEMINI_BASE}/{model.model_name}:generateContent"
        params = {"key": self.gemini_api_key}
        payload = {
            "contents": [
                {"parts": [{"text": prompt}]},
                {"parts": [{"text": query}]},
            ]
        }
        r = await self.client.post(url, params=params, json=payload)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            raise LLMProviderError(
                provider="gemini",
                status_code=exc.response.status_code,
                detail=detail,
            ) from exc
        body = r.json()
        candidates = body.get("candidates", [])
        text = ""
        if candidates:
            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        usage = body.get("usageMetadata", {})
        return LLMResponse(
            text=text,
            prompt_tokens=int(usage.get("promptTokenCount", 0)),
            completion_tokens=int(usage.get("candidatesTokenCount", 0)),
        )

    @staticmethod
    def calculate_cost(
        prompt_tokens: int, completion_tokens: int, model: ModelDefinition
    ) -> Decimal:
        return (
            Decimal(prompt_tokens) * model.input_cost_per_1k_tokens
            + Decimal(completion_tokens) * model.output_cost_per_1k_tokens
        ) / Decimal(1000)
