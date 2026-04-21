from __future__ import annotations

from typing import Any

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ModelLoadError(Exception):
    pass


class BARTSummarizer:
    _cache: dict[str, tuple[Any, Any]] = {}

    def __init__(
        self,
        model_name: str,
        max_length: int = 150,
        min_length: int = 50,
        do_sample: bool = False,
        device: str = "auto",
    ) -> None:
        self.model_name = model_name
        self.max_length = max_length
        self.min_length = min_length
        self.do_sample = do_sample
        self.device = self._resolve_device(device)
        self.tokenizer = None
        self.model = None

    def _resolve_device(self, device: str) -> str:
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device

    def load(self) -> None:
        cache_key = f"{self.model_name}:{self.device}"
        if cache_key in self._cache:
            self.tokenizer, self.model = self._cache[cache_key]
            return

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            self.model.to(self.device)
        except Exception as exc:
            raise ModelLoadError(f"Failed to load BART model '{self.model_name}': {exc}") from exc

        self._cache[cache_key] = (self.tokenizer, self.model)
        logger.info("Loaded BART model on %s", self.device)

    def summarize_chunk(self, text: str) -> str:
        if not self.model or not self.tokenizer:
            self.load()

        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=1024)
        inputs = {key: value.to(self.device) for key, value in inputs.items()}

        summary_ids = self.model.generate(
            **inputs,
            max_length=self.max_length,
            min_length=self.min_length,
            do_sample=self.do_sample,
        )
        return self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
