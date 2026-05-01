from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ModelConfig:
    reasoning: str
    execution: str
    coordinator: str
    finance: str
    hr: str
    planner: str
    executor: str
    summarizer: str


@dataclass(frozen=True)
class BudgetConfig:
    max_input_tokens: int
    max_output_tokens: int
    max_agent_turns: int
    compaction_chunk_tokens: int


@dataclass(frozen=True)
class MemoryConfig:
    token_threshold: int
    long_document_word_threshold: int
    compaction_ratio: float


@dataclass(frozen=True)
class CircuitBreakerConfig:
    threshold: int
    timeout_seconds: int


@dataclass(frozen=True)
class RateLimitConfig:
    max_retries: int
    backoff_base_seconds: float
    backoff_max_seconds: float


@dataclass(frozen=True)
class AppConfig:
    models: ModelConfig
    budgets: BudgetConfig
    memory: MemoryConfig
    circuit_breaker: CircuitBreakerConfig
    rate_limits: RateLimitConfig
    prompts: dict[str, str]
    database_path: Path
    log_file: Path
    log_level: str
    streamlit_port: int
    openai_api_key: str | None
    openrouter_api_key: str | None


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return int(raw)


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return float(raw)


def _path_from_env(name: str, default: str) -> Path:
    raw = os.getenv(name, default)
    path = Path(raw)
    return path if path.is_absolute() else ROOT_DIR / path


def load_config() -> AppConfig:
    load_dotenv(ROOT_DIR / ".env")
    model_yaml = _read_yaml(ROOT_DIR / "config" / "models.yml")
    prompt_yaml = _read_yaml(ROOT_DIR / "config" / "prompts.yml")

    models = model_yaml.get("models", {})
    budgets = model_yaml.get("budgets", {})
    memory = model_yaml.get("memory", {})
    breaker = model_yaml.get("circuit_breaker", {})
    rate_limits = model_yaml.get("rate_limits", {})

    reasoning = os.getenv("REASONING_MODEL", models.get("reasoning", "o3-mini"))
    execution = os.getenv("EXECUTION_MODEL", models.get("execution", "gpt-4o-mini"))

    return AppConfig(
        models=ModelConfig(
            reasoning=reasoning,
            execution=execution,
            coordinator=os.getenv("COORDINATOR_MODEL", models.get("coordinator", execution)),
            finance=os.getenv("FINANCE_MODEL", models.get("finance", execution)),
            hr=os.getenv("HR_MODEL", models.get("hr", execution)),
            planner=os.getenv("PLANNER_MODEL", models.get("planner", reasoning)),
            executor=os.getenv("EXECUTOR_MODEL", models.get("executor", execution)),
            summarizer=os.getenv("SUMMARIZER_MODEL", models.get("summarizer", execution)),
        ),
        budgets=BudgetConfig(
            max_input_tokens=_env_int("MAX_INPUT_TOKENS", int(budgets.get("max_input_tokens", 12000))),
            max_output_tokens=_env_int(
                "MAX_OUTPUT_TOKENS", int(budgets.get("max_output_tokens", 800))
            ),
            max_agent_turns=_env_int("MAX_AGENT_TURNS", int(budgets.get("max_agent_turns", 6))),
            compaction_chunk_tokens=_env_int(
                "COMPACTION_CHUNK_TOKENS", int(budgets.get("compaction_chunk_tokens", 3000))
            ),
        ),
        memory=MemoryConfig(
            token_threshold=_env_int(
                "MEMORY_TOKEN_THRESHOLD", int(memory.get("token_threshold", 6000))
            ),
            long_document_word_threshold=_env_int(
                "LONG_DOCUMENT_WORD_THRESHOLD",
                int(memory.get("long_document_word_threshold", 3000)),
            ),
            compaction_ratio=float(memory.get("compaction_ratio", 0.3)),
        ),
        circuit_breaker=CircuitBreakerConfig(
            threshold=_env_int(
                "CIRCUIT_BREAKER_THRESHOLD", int(breaker.get("threshold", 3))
            ),
            timeout_seconds=_env_int(
                "CIRCUIT_BREAKER_TIMEOUT", int(breaker.get("timeout_seconds", 60))
            ),
        ),
        rate_limits=RateLimitConfig(
            max_retries=_env_int("RATE_LIMIT_MAX_RETRIES", int(rate_limits.get("max_retries", 3))),
            backoff_base_seconds=_env_float(
                "RATE_LIMIT_BACKOFF_BASE_SECONDS",
                float(rate_limits.get("backoff_base_seconds", 1)),
            ),
            backoff_max_seconds=float(rate_limits.get("backoff_max_seconds", 10)),
        ),
        prompts={str(key): str(value) for key, value in prompt_yaml.items()},
        database_path=_path_from_env("DATABASE_PATH", "data/sessions.db"),
        log_file=_path_from_env("LOG_FILE", "logs/orchestration.log"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        streamlit_port=_env_int("STREAMLIT_PORT", 8501),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
    )
