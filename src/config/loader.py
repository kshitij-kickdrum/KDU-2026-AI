"""YAML configuration loading and LLM provider selection."""

from __future__ import annotations

import importlib
import os
from pathlib import Path
from collections.abc import Mapping
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import SecretStr

AGENT_FIELDS: Mapping[str, type[Any]] = {
    "role": str,
    "goal": str,
    "backstory": str,
    "tools": list,
}
TASK_FIELDS: Mapping[str, type[Any]] = {
    "description": str,
    "expected_output": str,
    "agent": str,
}


def get_config_paths() -> tuple[str, str]:
    """Return absolute paths to config/agents.yaml and config/tasks.yaml."""
    root = Path(__file__).resolve().parents[2]
    return str(root / "config" / "agents.yaml"), str(root / "config" / "tasks.yaml")


def _load_yaml(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("config: expected mapping")
    return data


def _validate(
    config: dict[str, Any], fields: Mapping[str, type[Any]], label: str
) -> None:
    if not isinstance(config, dict) or not config:
        raise ValueError(f"{label}: expected non-empty mapping")
    for name, values in config.items():
        if not isinstance(values, dict):
            raise ValueError(f"{name}: expected mapping")
        for field, expected in fields.items():
            if field not in values or not isinstance(values[field], expected):
                raise ValueError(f"{name}.{field}: expected {expected.__name__}")


def validate_agents_config(config: dict[str, Any]) -> None:
    """Validate parsed agents.yaml data."""
    _validate(config, AGENT_FIELDS, "agents")


def validate_tasks_config(config: dict[str, Any]) -> None:
    """Validate parsed tasks.yaml data."""
    _validate(config, TASK_FIELDS, "tasks")


def load_agents_config(path: str) -> dict[str, Any]:
    """Load and validate agent configuration."""
    config = _load_yaml(path)
    validate_agents_config(config)
    return config


def load_tasks_config(path: str) -> dict[str, Any]:
    """Load and validate task configuration."""
    config = _load_yaml(path)
    validate_tasks_config(config)
    return config


def get_llm_provider() -> Any:
    """Select OpenAI first, then OpenRouter, and validate Serper credentials."""
    load_dotenv()
    if not os.getenv("SERPER_API_KEY"):
        raise EnvironmentError("Missing required environment variable: SERPER_API_KEY")
    try:
        chat_openai = getattr(importlib.import_module("langchain_openai"), "ChatOpenAI")
    except Exception as exc:
        raise EnvironmentError("langchain-openai is not installed") from exc
    openai_key = os.getenv("OPENAI_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openai_key:
        return chat_openai(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=SecretStr(openai_key),
        )
    if openrouter_key:
        return chat_openai(
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo"),
            api_key=SecretStr(openrouter_key),
            base_url="https://openrouter.ai/api/v1",
        )
    raise EnvironmentError(
        "No LLM provider configured. Missing OPENAI_API_KEY or OPENROUTER_API_KEY"
    )
