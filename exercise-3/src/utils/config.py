from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    """Raised when configuration loading or validation fails."""


REQUIRED_MODEL_KEYS = {
    "bart": ["model_name", "max_length", "min_length", "do_sample"],
    "qwen": ["api_url", "timeout", "max_retries", "temperature", "max_tokens", "top_p", "model_name"],
    "roberta": ["model_name", "max_seq_length", "confidence_threshold"],
    "chunking": ["max_tokens", "overlap"],
    "summary_lengths": ["short", "medium", "long"],
}

REQUIRED_PROMPT_KEYS = [
    "merge_prompt",
    "refine_prompt",
    "qa_fallback_prompt",
    "refinement_strategies",
]


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        content = yaml.safe_load(handle) or {}
    if not isinstance(content, dict):
        raise ConfigError(f"Configuration file must contain a mapping: {path}")
    return content


def _validate_required(config: dict[str, Any], required: dict[str, list[str]], label: str) -> None:
    for section, keys in required.items():
        if section not in config:
            raise ConfigError(f"Missing section '{section}' in {label} config")
        for key in keys:
            if key not in config[section]:
                raise ConfigError(f"Missing key '{section}.{key}' in {label} config")


def _validate_prompts(config: dict[str, Any]) -> None:
    for key in REQUIRED_PROMPT_KEYS:
        if key not in config:
            raise ConfigError(f"Missing key '{key}' in prompts config")


def load_configs(base_dir: str | Path) -> dict[str, Any]:
    base_path = Path(base_dir)
    model_config = _load_yaml(base_path / "config" / "models.yaml")
    prompt_config = _load_yaml(base_path / "config" / "prompts.yaml")

    _validate_required(model_config, REQUIRED_MODEL_KEYS, "model")
    _validate_prompts(prompt_config)

    return {"models": model_config, "prompts": prompt_config}
