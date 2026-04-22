from __future__ import annotations

from typing import Any

from src.services.validation import ValidationService
from src.utils.logger import get_logger
from src.utils.token_counter import TokenCounter

logger = get_logger(__name__)


class QAService:
    def __init__(
        self,
        roberta_model: Any,
        qwen_client: Any,
        token_counter: TokenCounter,
        validation_service: ValidationService,
        confidence_threshold: float = 0.20,
        max_context_tokens: int = 512,
    ) -> None:
        self.roberta_model = roberta_model
        self.qwen_client = qwen_client
        self.token_counter = token_counter
        self.validation_service = validation_service
        self.confidence_threshold = confidence_threshold
        self.max_context_tokens = max_context_tokens

    def _run_roberta_attempt(self, level: int, context_type: str, question: str, context: str) -> dict[str, Any]:
        effective_context_type = context_type
        effective_context = context

        if self.token_counter.exceeds_combined_limit(question, context, self.max_context_tokens):
            logger.info("Context exceeds token limit at level %s; compressing", level)
            effective_context = self.qwen_client.compress_context(question, context)
            effective_context_type = "compressed"

        answer, confidence = self.roberta_model.answer_question(question, effective_context)

        if self.validation_service.validate_qa_confidence(confidence, self.confidence_threshold) and self.validation_service.validate_answer(answer):
            return {
                "success": True,
                "answer": answer,
                "confidence": confidence,
                "attempt": {
                    "level": level,
                    "model": "roberta",
                    "context_type": effective_context_type,
                    "confidence": confidence,
                    "result": "success",
                },
            }

        return {
            "success": False,
            "attempt": {
                "level": level,
                "model": "roberta",
                "context_type": effective_context_type,
                "confidence": confidence,
                "result": "low_confidence",
            },
        }

    def answer_question(self, question: str, base_summary: str, refined_summary: str | None = None) -> dict[str, Any]:
        attempts: list[dict[str, Any]] = []

        if refined_summary:
            level1 = self._run_roberta_attempt(1, "refined", question, refined_summary)
            attempts.append(level1["attempt"])
            if level1["success"]:
                return {
                    "answer": level1["answer"],
                    "confidence": level1["confidence"],
                    "model_used": "roberta",
                    "fallback_level": 1,
                    "error": None,
                    "suggestion": None,
                    "attempts": attempts,
                }

        level2 = self._run_roberta_attempt(2, "base", question, base_summary)
        attempts.append(level2["attempt"])
        if level2["success"]:
            return {
                "answer": level2["answer"],
                "confidence": level2["confidence"],
                "model_used": "roberta",
                "fallback_level": 2,
                "error": None,
                "suggestion": None,
                "attempts": attempts,
            }

        qwen_answer = self.qwen_client.generative_qa(question, base_summary)
        if qwen_answer.strip().lower() != "not found in context.":
            attempts.append(
                {
                    "level": 3,
                    "model": "qwen",
                    "context_type": "base",
                    "confidence": None,
                    "result": "success",
                }
            )
            return {
                "answer": qwen_answer,
                "confidence": 0.0,
                "model_used": "qwen_fallback",
                "fallback_level": 3,
                "error": None,
                "suggestion": None,
                "attempts": attempts,
            }

        attempts.append(
            {
                "level": 3,
                "model": "qwen",
                "context_type": "base",
                "confidence": None,
                "result": "not_found",
            }
        )
        return {
            "answer": None,
            "confidence": 0.0,
            "model_used": "qwen_fallback",
            "fallback_level": 4,
            "error": "Unable to answer this question from the provided text.",
            "suggestion": "Try rephrasing your question or asking about different aspects of the text.",
            "attempts": attempts,
        }
