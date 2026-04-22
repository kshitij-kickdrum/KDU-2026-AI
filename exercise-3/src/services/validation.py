from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)


class ValidationService:
    def __init__(self, min_summary_words: int = 50) -> None:
        self.min_summary_words = min_summary_words

    def _word_count(self, text: str) -> int:
        return len(text.split())

    def _sentence_count(self, text: str) -> int:
        sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
        return len(sentences)

    def _has_excessive_repetition(self, text: str, max_consecutive: int = 3) -> bool:
        words = [re.sub(r"[^\w]", "", w).lower() for w in text.split()]
        words = [w for w in words if w]
        consecutive = 1
        for idx in range(1, len(words)):
            if words[idx] == words[idx - 1]:
                consecutive += 1
                if consecutive > max_consecutive:
                    return True
            else:
                consecutive = 1
        return False

    def validate_summary(self, summary: str, input_word_count: int) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        summary_clean = summary.strip()
        summary_words = self._word_count(summary_clean)

        if not summary_clean:
            errors.append("Summary is empty")

        if summary_words < self.min_summary_words:
            errors.append(f"Summary must be at least {self.min_summary_words} words")

        ratio = (summary_words / input_word_count) if input_word_count > 0 else 0.0
        if ratio < 0.1 or ratio > 0.5:
            warnings.append("Compression ratio is outside recommended 0.1-0.5 range")

        if self._has_excessive_repetition(summary_clean):
            errors.append("Summary contains excessive consecutive repeated words")

        sentence_count = self._sentence_count(summary_clean)
        if sentence_count < 2:
            errors.append("Summary must contain at least 2 sentences")

        return ValidationResult(
            is_valid=not errors,
            errors=errors,
            warnings=warnings,
            metrics={
                "summary_words": float(summary_words),
                "sentence_count": float(sentence_count),
                "compression_ratio": ratio,
            },
        )

    def validate_qa_confidence(self, confidence: float, threshold: float = 0.20) -> bool:
        return isinstance(confidence, (int, float)) and 0.0 <= confidence <= 1.0 and confidence >= threshold

    def validate_answer(self, answer: str) -> bool:
        return bool(answer and len(answer.split()) >= 3)
