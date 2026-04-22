from src.services.chunking import ChunkingService
from src.services.summarization import AdaptiveLengthCalculator, SummarizationService
from src.services.validation import ValidationService
from src.utils.token_counter import TokenCounter


class FakeBART:
    def summarize_chunk(self, text: str) -> str:
        return "chunk-summary " + " ".join(text.split()[:10])


class FakeQwen:
    def merge_summaries(self, summaries):
        return " ".join(summaries)

    def refine_summary(self, base_summary, length_type, target_words, min_words, max_words):
        words = base_summary.split()
        return " ".join(words[:max(target_words, 1)])


def test_adaptive_length_calculator():
    calc = AdaptiveLengthCalculator(
        {
            "short": {"compression_ratio": [0.05, 0.08], "min_words": 80, "max_words": 250},
            "medium": {"compression_ratio": [0.10, 0.15], "min_words": 150, "max_words": 500},
            "long": {"compression_ratio": [0.20, 0.30], "min_words": 300, "max_words": 800},
        }
    )
    out = calc.calculate_target_length(2000, "short")
    assert out["min_words"] == 100
    assert out["max_words"] == 160
    assert out["target_words"] == 130


def test_summarization_pipeline_base_and_refine():
    counter = TokenCounter(max_tokens=512)
    chunking = ChunkingService(counter, max_tokens=50, overlap=5)
    validator = ValidationService(min_summary_words=2)
    calc = AdaptiveLengthCalculator(
        {
            "short": {"compression_ratio": [0.05, 0.08], "min_words": 5, "max_words": 20},
            "medium": {"compression_ratio": [0.10, 0.15], "min_words": 8, "max_words": 40},
            "long": {"compression_ratio": [0.20, 0.30], "min_words": 12, "max_words": 60},
        }
    )
    service = SummarizationService(chunking, FakeBART(), FakeQwen(), validator, calc)

    text = (
        "Artificial intelligence is a field focused on building systems that can reason and learn. "
        "It includes machine learning, planning, and natural language processing.\n\n"
        "Modern AI applications include recommendation systems, coding assistants, and autonomous workflows."
    )

    base = service.generate_base_summary(text)
    assert base["base_summary"]
    assert base["chunk_count"] >= 1

    refined = service.refine_summary(base["base_summary"], "medium", base["input_word_count"])
    assert refined["refined_summary"]
    assert "target" in refined["target_range"]
