from __future__ import annotations

import time
from typing import Any

import httpx

from src.utils.logger import get_logger

logger = get_logger(__name__)


class QwenClient:
    def __init__(
        self,
        api_url: str,
        model_name: str,
        timeout: int = 30,
        max_retries: int = 3,
        temperature: float = 0.3,
        max_tokens: int = 512,
        top_p: float = 0.9,
        prompts: dict[str, Any] | None = None,
    ) -> None:
        self.api_url = api_url
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.prompts = prompts or {}

    def _chat(self, prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }

        backoff = 1.0
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(self.api_url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
            except Exception as exc:
                last_error = exc
                logger.warning("Qwen request failed (attempt %s/%s): %s", attempt, self.max_retries, exc)
                if attempt < self.max_retries:
                    time.sleep(backoff)
                    backoff *= 2

        raise RuntimeError(f"Qwen request failed after {self.max_retries} attempts: {last_error}")

    def health_check(self) -> bool:
        try:
            _ = self._chat("Reply with: ok")
            return True
        except Exception:
            return False

    def merge_summaries(self, summaries: list[str]) -> str:
        template = self.prompts.get(
            "merge_prompt",
            "Merge the summaries into one coherent summary:\n{chunk_summaries}",
        )
        prompt = template.format(chunk_summaries="\n\n".join(summaries))
        return self._chat(prompt)

    def refine_summary(
        self,
        base_summary: str,
        length_type: str,
        target_words: int,
        min_words: int,
        max_words: int,
    ) -> str:
        strategy = self.prompts.get("refinement_strategies", {}).get(length_type, "Keep core information and remove redundancy.")
        template = self.prompts.get(
            "refine_prompt",
            "Refine summary to {target_words} words:\n{base_summary}",
        )
        prompt = template.format(
            length_type=length_type,
            target_words=target_words,
            min_words=min_words,
            max_words=max_words,
            strategy_guidelines=strategy,
            base_summary=base_summary,
        )
        return self._chat(prompt)

    def compress_context(self, question: str, summary: str) -> str:
        prompt = (
            "Compress this context for question-answering while preserving facts needed "
            f"to answer the question.\n\nQuestion: {question}\n\nContext:\n{summary}\n\nCompressed context:"
        )
        return self._chat(prompt)

    def generative_qa(self, question: str, summary: str) -> str:
        template = self.prompts.get(
            "qa_fallback_prompt",
            "Answer question from context only. If missing, reply: Not found in context.\nContext:\n{summary}\nQuestion:{question}",
        )
        prompt = template.format(summary=summary, question=question)
        return self._chat(prompt)
