from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.services.chunking import ChunkingService
from src.services.validation import ValidationService
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AdaptiveLengthCalculator:
    summary_lengths_config: dict[str, dict[str, Any]]

    def calculate_target_length(self, input_word_count: int, length_type: str) -> dict[str, int]:
        if length_type not in self.summary_lengths_config:
            raise ValueError(f"Unsupported length type: {length_type}")

        config = self.summary_lengths_config[length_type]
        min_ratio, max_ratio = config["compression_ratio"]
        min_bound = int(config["min_words"])
        max_bound = int(config["max_words"])

        min_words = max(int(input_word_count * min_ratio), min_bound)
        max_words = min(int(input_word_count * max_ratio), max_bound)

        if min_words > max_bound:
            min_words = max_bound
        if max_words < min_bound:
            max_words = min_bound

        target_words = (min_words + max_words) // 2

        return {"min_words": min_words, "max_words": max_words, "target_words": target_words}


class SummarizationService:
    def __init__(
        self,
        chunking_service: ChunkingService,
        bart_model: Any,
        qwen_client: Any,
        validation_service: ValidationService,
        length_calculator: AdaptiveLengthCalculator,
    ) -> None:
        self.chunking_service = chunking_service
        self.bart_model = bart_model
        self.qwen_client = qwen_client
        self.validation_service = validation_service
        self.length_calculator = length_calculator

    def _merge_recursive(self, summaries: list[str], batch_size: int = 4) -> str:
        if not summaries:
            return ""
        if len(summaries) == 1:
            return summaries[0]

        round_summaries: list[str] = []
        for idx in range(0, len(summaries), batch_size):
            group = summaries[idx : idx + batch_size]
            round_summaries.append(self.qwen_client.merge_summaries(group))
        return self._merge_recursive(round_summaries, batch_size=batch_size)

    def generate_base_summary(self, text: str) -> dict[str, Any]:
        input_word_count = len(text.split())
        chunks = self.chunking_service.chunk_text(text)
        logger.info("Chunked input into %s chunks", len(chunks))

        chunk_summaries: list[str] = []
        for chunk in chunks:
            chunk_summaries.append(self.bart_model.summarize_chunk(chunk.text))

        base_summary = self._merge_recursive(chunk_summaries)
        validation = self.validation_service.validate_summary(base_summary, input_word_count)
        if not validation.is_valid:
            logger.warning("Base summary validation errors: %s", validation.errors)

        return {
            "base_summary": base_summary,
            "input_word_count": input_word_count,
            "word_count": len(base_summary.split()),
            "chunk_count": len(chunks),
            "validation": validation,
        }

    def refine_summary(self, base_summary: str, length_type: str, input_word_count: int) -> dict[str, Any]:
        target = self.length_calculator.calculate_target_length(input_word_count, length_type)
        refined = self.qwen_client.refine_summary(
            base_summary=base_summary,
            length_type=length_type,
            target_words=target["target_words"],
            min_words=target["min_words"],
            max_words=target["max_words"],
        )

        validation = self.validation_service.validate_summary(refined, input_word_count)
        if not validation.is_valid:
            logger.warning("Refined summary validation errors: %s", validation.errors)

        return {
            "refined_summary": refined,
            "word_count": len(refined.split()),
            "target_range": {
                "min": target["min_words"],
                "max": target["max_words"],
                "target": target["target_words"],
            },
            "compression_ratio": (len(refined.split()) / input_word_count) if input_word_count else 0.0,
            "validation": validation,
        }
