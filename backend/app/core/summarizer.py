from __future__ import annotations

from dataclasses import dataclass

from app.core.llm_client import LLMClient


@dataclass(slots=True)
class SummarizeResult:
    text: str
    was_summarized: bool
    original_word_count: int
    summarized_word_count: int


class QuerySummarizer:
    def __init__(
        self,
        llm_client: LLMClient,
        model_key: str = "gemini-flash-lite",
        threshold_words: int = 80,
    ) -> None:
        self.llm_client = llm_client
        self.model_key = model_key
        self.threshold_words = threshold_words

    async def maybe_summarize(self, query: str) -> SummarizeResult:
        original_words = len(query.split())
        if original_words <= self.threshold_words:
            return SummarizeResult(
                text=query,
                was_summarized=False,
                original_word_count=original_words,
                summarized_word_count=original_words,
            )
        summary = await self.llm_client.summarize_with_gemini(self.model_key, query)
        summary_words = len(summary.split())
        return SummarizeResult(
            text=summary,
            was_summarized=True,
            original_word_count=original_words,
            summarized_word_count=summary_words,
        )
