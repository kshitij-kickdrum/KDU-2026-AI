from __future__ import annotations

import pytest

from app.core.summarizer import QuerySummarizer


class StubLLM:
    async def summarize_with_gemini(self, model_key: str, text: str) -> str:
        return "short summary"


@pytest.mark.asyncio
async def test_summarizer_threshold_behavior() -> None:
    summarizer = QuerySummarizer(llm_client=StubLLM(), threshold_words=5)
    short = await summarizer.maybe_summarize("one two three")
    assert short.was_summarized is False
    long = await summarizer.maybe_summarize("one two three four five six seven")
    assert long.was_summarized is True
