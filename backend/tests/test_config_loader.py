from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from app.core.config_loader import ConfigError, ConfigLoader


def _write_yaml(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as fp:
        yaml.safe_dump(data, fp, sort_keys=False)


def _make_valid_files(base: Path) -> tuple[Path, Path]:
    config_dir = base / "config"
    prompts_dir = base / "prompts"
    config_dir.mkdir(parents=True)
    prompts_dir.mkdir(parents=True)
    _write_yaml(
        config_dir / "settings.yaml",
        {
            "app": {
                "name": "x",
                "environment": "test",
                "log_level": "INFO",
                "database_path": "data/test.db",
            },
            "features": {
                "enable_llm_classification_fallback": True,
                "enable_cost_tracking": True,
                "enable_budget_enforcement": True,
                "enable_response_cache": True,
                "enable_pre_summarization": True,
            },
            "limits": {"rate_limit_requests_per_minute": 100},
        },
    )
    _write_yaml(
        config_dir / "models.yaml",
        {
            "models": {
                "gemini-flash-lite": {
                    "provider": "gemini",
                    "model_name": "gemini-2.0-flash-lite",
                    "input_cost_per_1k_tokens": 0.1,
                    "output_cost_per_1k_tokens": 0.2,
                    "max_tokens": 1024,
                    "timeout_seconds": 30,
                }
            }
        },
    )
    _write_yaml(
        config_dir / "routing.yaml",
        {
            "routing": {
                "faq": {"low": "gemini-flash-lite", "medium": "gemini-flash-lite", "high": "gemini-flash-lite"},
                "complaint": {"low": "gemini-flash-lite", "medium": "gemini-flash-lite", "high": "gemini-flash-lite"},
                "booking": {"low": "gemini-flash-lite", "medium": "gemini-flash-lite", "high": "gemini-flash-lite"},
            },
            "fallback": {"cheapest_model": "gemini-flash-lite"},
        },
    )
    _write_yaml(
        config_dir / "budget.yaml",
        {"budget": {"daily_limit_usd": 1.0, "monthly_limit_usd": 20.0, "warning_threshold_ratio": 0.8}},
    )
    _write_yaml(
        prompts_dir / "registry.yaml",
        {
            "registry": {
                "faq": {"active_version": "v1", "available_versions": ["v1"]},
                "complaint": {"active_version": "v1", "available_versions": ["v1"]},
                "booking": {"active_version": "v1", "available_versions": ["v1"]},
                "classifier": {"active_version": "v1", "available_versions": ["v1"]},
            }
        },
    )
    return config_dir, prompts_dir


def test_config_load_and_validation(workspace_tmp_dir: Path) -> None:
    config_dir, prompts_dir = _make_valid_files(workspace_tmp_dir)
    loader = ConfigLoader(str(config_dir), str(prompts_dir))
    runtime = loader.load()
    assert runtime.settings.app.name == "x"


def test_config_rejects_invalid(workspace_tmp_dir: Path) -> None:
    config_dir, prompts_dir = _make_valid_files(workspace_tmp_dir)
    _write_yaml(config_dir / "budget.yaml", {"budget": {"daily_limit_usd": -1}})
    loader = ConfigLoader(str(config_dir), str(prompts_dir))
    with pytest.raises(ConfigError):
        loader.load()


def test_hot_reload_preserves_last_good(workspace_tmp_dir: Path) -> None:
    config_dir, prompts_dir = _make_valid_files(workspace_tmp_dir)
    loader = ConfigLoader(str(config_dir), str(prompts_dir))
    loader.load()
    _write_yaml(config_dir / "budget.yaml", {"budget": {"daily_limit_usd": -1}})
    with pytest.raises(ConfigError):
        loader.reload()
    assert loader.runtime.settings.app.name == "x"


@pytest.mark.parametrize("app_name", ["fixit", "x", "svc-01"])
def test_property_configuration_loading_consistency(
    app_name: str, workspace_tmp_dir: Path
) -> None:
    config_dir, prompts_dir = _make_valid_files(workspace_tmp_dir)
    settings = yaml.safe_load((config_dir / "settings.yaml").read_text(encoding="utf-8"))
    settings["app"]["name"] = app_name
    _write_yaml(config_dir / "settings.yaml", settings)
    loader = ConfigLoader(str(config_dir), str(prompts_dir))
    runtime = loader.load()
    dumped = runtime.model_dump()
    assert dumped["settings"]["app"]["name"] == app_name
