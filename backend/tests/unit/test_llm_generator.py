from src.components.llm_generator import LLMGenerator
from src.models import Chunk, ChunkMetadata, RetrievalResult


def _ctx(content: str, score: float = 0.7) -> RetrievalResult:
    chunk = Chunk(
        document_id="d1",
        content=content,
        token_count=max(1, len(content.split())),
        start_index=0,
        end_index=len(content),
        metadata=ChunkMetadata(document_title="Doc", document_source="doc.pdf"),
    )
    return RetrievalResult(chunk=chunk, combined_score=score, semantic_score=score, keyword_score=score)


def test_llm_no_context_fallback(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    gen = LLMGenerator(provider="openrouter", model="openai/gpt-4o-mini")
    resp = gen.generate_response("what is attention", [])
    assert "enough information" in resp.answer.lower()
    assert "no_context" in resp.warnings


def test_llm_insufficient_context_detection(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    gen = LLMGenerator(provider="openrouter", model="openai/gpt-4o-mini")
    resp = gen.generate_response("attention transformers", [_ctx("completely unrelated text about cooking")])
    assert "insufficient_context_coverage" in resp.warnings


def test_llm_unique_sources(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    gen = LLMGenerator(provider="openrouter", model="openai/gpt-4o-mini")
    ctx = [_ctx("attention in transformers"), _ctx("multi head attention")]
    resp = gen._fallback_answer("q", ctx)  # noqa: SLF001
    assert len(resp.sources) == 1
