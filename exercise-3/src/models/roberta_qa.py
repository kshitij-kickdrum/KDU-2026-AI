from __future__ import annotations

from typing import Any

import torch
from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ModelLoadError(Exception):
    pass


class RoBERTaQA:
    _cache: dict[str, Any] = {}

    def __init__(self, model_name: str, max_seq_length: int = 512, device: str = "auto") -> None:
        self.model_name = model_name
        self.max_seq_length = max_seq_length
        self.device = self._resolve_device(device)
        self.qa_pipeline = None

    def _resolve_device(self, device: str) -> int:
        if device == "auto":
            return 0 if torch.cuda.is_available() else -1
        return 0 if device == "cuda" else -1

    def load(self) -> None:
        cache_key = f"{self.model_name}:{self.device}"
        if cache_key in self._cache:
            self.qa_pipeline = self._cache[cache_key]
            return

        try:
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForQuestionAnswering.from_pretrained(self.model_name)
            self.qa_pipeline = pipeline(
                "question-answering",
                model=model,
                tokenizer=tokenizer,
                device=self.device,
            )
        except Exception as exc:
            raise ModelLoadError(f"Failed to load RoBERTa QA model '{self.model_name}': {exc}") from exc

        self._cache[cache_key] = self.qa_pipeline
        logger.info("Loaded RoBERTa QA model")

    def answer_question(self, question: str, context: str) -> tuple[str, float]:
        if self.qa_pipeline is None:
            self.load()

        result = self.qa_pipeline(question=question, context=context)
        answer = str(result.get("answer", "")).strip()
        score = float(result.get("score", 0.0))
        return answer, score
