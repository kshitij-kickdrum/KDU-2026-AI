from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.models.bart_summarizer import BARTSummarizer
from src.models.qwen_client import QwenClient
from src.models.roberta_qa import RoBERTaQA
from src.services.chunking import ChunkingService
from src.services.qa_service import QAService
from src.services.session_store import InMemorySessionStore
from src.services.summarization import AdaptiveLengthCalculator, SummarizationService
from src.services.validation import ValidationService
from src.utils.config import load_configs
from src.utils.token_counter import TokenCounter


@dataclass
class ServiceContainer:
    config: dict[str, Any]
    prompts: dict[str, Any]
    token_counter: TokenCounter
    chunking_service: ChunkingService
    validation_service: ValidationService
    bart_model: BARTSummarizer
    qwen_client: QwenClient
    roberta_model: RoBERTaQA
    summarization_service: SummarizationService
    qa_service: QAService
    session_store: InMemorySessionStore
    startup_time: float



def build_container(project_root: str | Path) -> ServiceContainer:
    configs = load_configs(project_root)
    model_cfg = configs["models"]
    prompts = configs["prompts"]

    token_counter = TokenCounter(max_tokens=model_cfg["roberta"]["max_seq_length"])
    chunking_service = ChunkingService(
        token_counter=token_counter,
        max_tokens=model_cfg["chunking"]["max_tokens"],
        overlap=model_cfg["chunking"]["overlap"],
    )
    validation_service = ValidationService(min_summary_words=50)

    bart = BARTSummarizer(**model_cfg["bart"])
    qwen = QwenClient(prompts=prompts, **model_cfg["qwen"])
    roberta_cfg = model_cfg["roberta"]
    roberta = RoBERTaQA(
        model_name=roberta_cfg["model_name"],
        max_seq_length=roberta_cfg["max_seq_length"],
        device=roberta_cfg.get("device", "auto"),
    )

    calc = AdaptiveLengthCalculator(summary_lengths_config=model_cfg["summary_lengths"])
    summarization = SummarizationService(
        chunking_service=chunking_service,
        bart_model=bart,
        qwen_client=qwen,
        validation_service=validation_service,
        length_calculator=calc,
    )
    qa = QAService(
        roberta_model=roberta,
        qwen_client=qwen,
        token_counter=token_counter,
        validation_service=validation_service,
        confidence_threshold=roberta_cfg["confidence_threshold"],
        max_context_tokens=roberta_cfg["max_seq_length"],
    )

    return ServiceContainer(
        config=model_cfg,
        prompts=prompts,
        token_counter=token_counter,
        chunking_service=chunking_service,
        validation_service=validation_service,
        bart_model=bart,
        qwen_client=qwen,
        roberta_model=roberta,
        summarization_service=summarization,
        qa_service=qa,
        session_store=InMemorySessionStore(ttl_minutes=60),
        startup_time=time.time(),
    )
