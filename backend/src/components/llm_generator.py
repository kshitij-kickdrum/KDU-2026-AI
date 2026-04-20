from __future__ import annotations

import os
import time

from src.models import GeneratedResponse, RetrievalResult
from src.utils.resilience import CircuitBreaker, retry

try:
    from openai import OpenAI
except Exception:  # noqa: BLE001
    OpenAI = None  # type: ignore[assignment]


class LLMGenerator:
    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-3.5-turbo",
        fallback_model: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 800,
        timeout_seconds: int = 30,
    ) -> None:
        self.provider = provider
        self.model = model
        self.fallback_model = fallback_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.breaker = CircuitBreaker()
        self.client = None

        if OpenAI:
            if provider == "openrouter":
                self.client = OpenAI(
                    api_key=os.getenv("OPENROUTER_API_KEY"),
                    base_url=base_url or "https://openrouter.ai/api/v1",
                    default_headers={
                        "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "http://localhost"),
                        "X-Title": os.getenv("OPENROUTER_APP_NAME", "hybrid-rag-chatbot"),
                    },
                )
            else:
                self.client = OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=base_url,
                )

    def _build_context(self, context: list[RetrievalResult]) -> str:
        lines = []
        for idx, item in enumerate(context, start=1):
            lines.append(
                f"[{idx}] {item.chunk.metadata.document_title or 'Document'} | "
                f"{item.chunk.metadata.section_title}\n{item.chunk.content}"
            )
        return "\n\n".join(lines)

    def _fallback_answer(self, query: str, context: list[RetrievalResult]) -> GeneratedResponse:
        if not context:
            return GeneratedResponse(
                answer="I don't have enough information in the provided documents.",
                confidence_score=0.0,
                context_used=[],
                sources=[],
                warnings=["no_context"],
                processing_time=0.0,
            )
        excerpts = " ".join(item.chunk.content[:220] for item in context[:3]).strip()
        sources = self._unique_sources(context)
        return GeneratedResponse(
            answer=f"Based on retrieved context, relevant information is: {excerpts}",
            confidence_score=min(0.85, max(0.3, context[0].combined_score)),
            context_used=[item.chunk for item in context],
            sources=sources,
            warnings=["llm_fallback_mode"],
            processing_time=0.0,
        )

    def _detect_insufficient_context(self, context: list[RetrievalResult], query: str) -> bool:
        q_terms = {t for t in query.lower().split() if len(t) > 2}
        if not q_terms:
            return False
        joined = " ".join(item.chunk.content.lower() for item in context)
        coverage = sum(1 for t in q_terms if t in joined) / max(1, len(q_terms))
        return coverage < 0.2

    def _detect_contradictions(self, context: list[RetrievalResult]) -> bool:
        if len(context) < 2:
            return False
        texts = [item.chunk.content.lower() for item in context]
        polarity_pairs = [(" is ", " is not "), (" are ", " are not "), (" can ", " cannot ")]
        for i, a in enumerate(texts):
            for b in texts[i + 1 :]:
                for pos, neg in polarity_pairs:
                    if pos in a and neg in b:
                        return True
                    if neg in a and pos in b:
                        return True
        return False

    def generate_response(self, query: str, context: list[RetrievalResult]) -> GeneratedResponse:
        start = time.perf_counter()
        if not context:
            return self._fallback_answer(query, context)
        if self._detect_insufficient_context(context, query):
            response = self._fallback_answer(query, [])
            response.warnings.append("insufficient_context_coverage")
            response.processing_time = time.perf_counter() - start
            return response
        if not self.client or not self.breaker.can_call():
            response = self._fallback_answer(query, context)
            response.processing_time = time.perf_counter() - start
            return response

        context_block = self._build_context(context)
        system_prompt = (
            "You are a helpful assistant. Answer using only the provided context. "
            "If insufficient, say exactly: I don't have enough information. "
            "Always cite source indices like [1], [2]."
        )
        user_prompt = f"Context:\n{context_block}\n\nQuestion:\n{query}\n\nAnswer:"

        def _call(model_name: str) -> str:
            chat = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout_seconds,
            )
            return chat.choices[0].message.content or "I don't have enough information."

        try:
            answer = retry(lambda: _call(self.model), attempts=3)
            self.breaker.on_success()
            warnings: list[str] = []
            if self._detect_contradictions(context):
                warnings.append("context_contains_possible_contradictions")
                answer = f"Note: sources may contain conflicting statements.\n\n{answer}"
            if "[" not in answer or "]" not in answer:
                warnings.append("missing_source_citation_format")
            return GeneratedResponse(
                answer=answer,
                confidence_score=min(0.95, max(0.4, context[0].combined_score)),
                context_used=[item.chunk for item in context],
                sources=self._unique_sources(context),
                processing_time=time.perf_counter() - start,
                warnings=warnings,
            )
        except Exception:  # noqa: BLE001
            if self.fallback_model:
                try:
                    answer = retry(lambda: _call(self.fallback_model or self.model), attempts=2)
                    self.breaker.on_success()
                    return GeneratedResponse(
                        answer=answer,
                        confidence_score=min(0.9, max(0.35, context[0].combined_score)),
                        context_used=[item.chunk for item in context],
                        sources=self._unique_sources(context),
                        processing_time=time.perf_counter() - start,
                        warnings=["primary_model_failed_used_fallback"],
                    )
                except Exception:  # noqa: BLE001
                    pass
            self.breaker.on_failure()
            response = self._fallback_answer(query, context)
            response.warnings.append("llm_api_failure")
            response.processing_time = time.perf_counter() - start
            return response

    def _unique_sources(self, context: list[RetrievalResult]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for item in context:
            source = item.chunk.metadata.document_source
            if source and source not in seen:
                out.append(source)
                seen.add(source)
        return out
