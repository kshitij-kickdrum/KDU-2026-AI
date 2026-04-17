from __future__ import annotations

import html
from pathlib import Path

import yaml

from app.core.config_loader import ConfigLoader
from app.models.config import PromptTemplateConfig


class PromptManager:
    def __init__(self, config_loader: ConfigLoader, prompts_dir: str = "prompts") -> None:
        self.config_loader = config_loader
        self.prompts_dir = Path(prompts_dir)

    @staticmethod
    def sanitize_input(text: str) -> str:
        escaped = text.replace("{", "{{").replace("}", "}}")
        return html.escape(escaped, quote=False)

    def get_active_version(self, category: str) -> str:
        registry = self.config_loader.runtime.prompt_registry.registry
        return registry[category].active_version

    def activate_version(self, category: str, version: str) -> tuple[str, str]:
        registry_path = self.prompts_dir / "registry.yaml"
        with registry_path.open("r", encoding="utf-8") as fp:
            data = yaml.safe_load(fp) or {}
        category_entry = data["registry"][category]
        if version not in category_entry["available_versions"]:
            raise ValueError(f"Version {version} not available for {category}")
        previous = category_entry["active_version"]
        category_entry["active_version"] = version
        with registry_path.open("w", encoding="utf-8") as fp:
            yaml.safe_dump(data, fp, sort_keys=False)
        self.config_loader.reload()
        return previous, version

    def render(self, category: str, query: str) -> tuple[str, str]:
        version = self.get_active_version(category)
        file_path = self.prompts_dir / category / f"{version}.yaml"
        with file_path.open("r", encoding="utf-8") as fp:
            data = yaml.safe_load(fp) or {}
        template = PromptTemplateConfig.model_validate(data).template
        safe_query = self.sanitize_input(query)
        return template.format(query=safe_query), version
