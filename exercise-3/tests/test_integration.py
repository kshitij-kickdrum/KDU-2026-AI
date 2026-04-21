from src.services.chunking import ChunkingService
from src.services.qa_service import QAService
from src.services.summarization import AdaptiveLengthCalculator, SummarizationService
from src.services.validation import ValidationService
from src.utils.token_counter import TokenCounter


class FakeBART:
    def summarize_chunk(self, text: str) -> str:
        return "chunk " + " ".join(text.split()[:12])


class FakeQwen:
    def merge_summaries(self, summaries):
        return " ".join(summaries)

    def refine_summary(self, base_summary, length_type, target_words, min_words, max_words):
        return " ".join(base_summary.split()[:target_words])

    def compress_context(self, question, summary):
        return " ".join(summary.split()[:100])

    def generative_qa(self, question, summary):
        if "missing" in question.lower():
            return "Not found in context."
        return "Generated answer from fallback"


class FakeRoberta:
    def __init__(self, low_first: bool = False):
        self.low_first = low_first
        self.calls = 0

    def answer_question(self, question, context):
        self.calls += 1
        if self.low_first and self.calls == 1:
            return "", 0.1
        return "Extracted answer", 0.7


def test_integration_full_summarization_and_qa_flow():
    token_counter = TokenCounter(max_tokens=100)
    chunking = ChunkingService(token_counter=token_counter, max_tokens=40, overlap=5)
    validation = ValidationService(min_summary_words=2)
    lengths = {
        "short": {"compression_ratio": [0.05, 0.08], "min_words": 5, "max_words": 20},
        "medium": {"compression_ratio": [0.10, 0.15], "min_words": 8, "max_words": 40},
        "long": {"compression_ratio": [0.20, 0.30], "min_words": 12, "max_words": 60},
    }

    summarization = SummarizationService(
        chunking_service=chunking,
        bart_model=FakeBART(),
        qwen_client=FakeQwen(),
        validation_service=validation,
        length_calculator=AdaptiveLengthCalculator(lengths),
    )

    qa = QAService(
        roberta_model=FakeRoberta(low_first=True),
        qwen_client=FakeQwen(),
        token_counter=token_counter,
        validation_service=validation,
        confidence_threshold=0.2,
        max_context_tokens=100,
    )

    text = (
        "AI systems can learn patterns from data and generalize to similar tasks. "
        "They are used in healthcare, finance, and education for decision support.\n\n"
        "Reliable deployment requires validation, monitoring, and human oversight."
    )

    base = summarization.generate_base_summary(text)
    refined = summarization.refine_summary(base["base_summary"], "medium", base["input_word_count"])

    result = qa.answer_question(
        question="Where are AI systems used?",
        base_summary=base["base_summary"],
        refined_summary=refined["refined_summary"],
    )

    assert base["base_summary"]
    assert refined["refined_summary"]
    assert result["answer"]
    assert result["fallback_level"] in {1, 2, 3}
