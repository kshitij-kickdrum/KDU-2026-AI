from __future__ import annotations

from pathlib import Path
from typing import Any
from collections.abc import Callable

import yaml


class ConfigManager:
    def __init__(self, config_path: str | Path = "config/config.yaml") -> None:
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self._callbacks: dict[str, list[Callable[[Any], None]]] = {}

    def load_config(self) -> dict[str, Any]:
        with self.config_path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}

    def get(self, key_path: str, default: Any = None) -> Any:
        value: Any = self.config
        for key in key_path.split("."):
            if not isinstance(value, dict):
                return default
            value = value.get(key)
            if value is None:
                return default
        return value

    def update(self, key_path: str, value: Any) -> None:
        keys = key_path.split(".")
        data = self.config
        for key in keys[:-1]:
            if key not in data or not isinstance(data[key], dict):
                data[key] = {}
            data = data[key]
        data[keys[-1]] = value
        with self.config_path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(self.config, fh, sort_keys=False)
        for callback in self._callbacks.get(key_path, []):
            callback(value)

    def validate(self) -> list[str]:
        errors: list[str] = []
        chunk_min = self.get("chunking.min_chunk_size", 100)
        chunk_max = self.get("chunking.max_chunk_size", 600)
        overlap = self.get("chunking.chunk_overlap", 60)
        if chunk_min <= 0:
            errors.append("chunking.min_chunk_size must be > 0")
        if chunk_max < chunk_min:
            errors.append("chunking.max_chunk_size must be >= min_chunk_size")
        if overlap < 0:
            errors.append("chunking.chunk_overlap must be >= 0")
        sw = self.get("search.semantic_weight", 0.6)
        kw = self.get("search.keyword_weight", 0.4)
        if sw < 0 or kw < 0:
            errors.append("search weights must be non-negative")
        if sw + kw <= 0:
            errors.append("at least one search weight must be > 0")
        return errors

    def reload(self) -> list[str]:
        self.config = self.load_config()
        return self.validate()

    def on_change(self, key_path: str, callback: Callable[[Any], None]) -> None:
        self._callbacks.setdefault(key_path, []).append(callback)
