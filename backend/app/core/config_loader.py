from __future__ import annotations

import copy
from pathlib import Path

import yaml
from pydantic import ValidationError

from app.models.config import (
    BudgetConfig,
    ModelsConfig,
    PromptRegistryConfig,
    RoutingConfig,
    RuntimeConfig,
    SettingsConfig,
)


class ConfigError(RuntimeError):
    pass


class ConfigLoader:
    def __init__(self, config_dir: str = "config", prompts_dir: str = "prompts") -> None:
        self.config_dir = Path(config_dir)
        self.prompts_dir = Path(prompts_dir)
        self._runtime_config: RuntimeConfig | None = None
        self._last_good_config: RuntimeConfig | None = None

    @property
    def runtime(self) -> RuntimeConfig:
        if self._runtime_config is None:
            self.load()
        assert self._runtime_config is not None
        return self._runtime_config

    def _read_yaml(self, path: Path) -> dict:
        try:
            with path.open("r", encoding="utf-8") as fp:
                content = yaml.safe_load(fp) or {}
        except yaml.YAMLError as exc:
            raise ConfigError(f"Invalid YAML in {path}: {exc}") from exc
        if not isinstance(content, dict):
            raise ConfigError(f"YAML root must be a mapping in {path}")
        return content

    def load(self) -> RuntimeConfig:
        try:
            settings = SettingsConfig.model_validate(
                self._read_yaml(self.config_dir / "settings.yaml")
            )
            models = ModelsConfig.model_validate(
                self._read_yaml(self.config_dir / "models.yaml")
            )
            routing = RoutingConfig.model_validate(
                self._read_yaml(self.config_dir / "routing.yaml")
            )
            budget = BudgetConfig.model_validate(
                self._read_yaml(self.config_dir / "budget.yaml")
            )
            prompt_registry = PromptRegistryConfig.model_validate(
                self._read_yaml(self.prompts_dir / "registry.yaml")
            )
        except ValidationError as exc:
            raise ConfigError(f"Configuration validation failed: {exc}") from exc

        runtime = RuntimeConfig(
            settings=settings,
            models=models,
            routing=routing,
            budget=budget,
            prompt_registry=prompt_registry,
        )
        self._runtime_config = runtime
        self._last_good_config = copy.deepcopy(runtime)
        return runtime

    def reload(self) -> RuntimeConfig:
        previous = self._last_good_config
        try:
            return self.load()
        except Exception:
            if previous is not None:
                self._runtime_config = copy.deepcopy(previous)
            raise
