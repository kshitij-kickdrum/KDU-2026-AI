from __future__ import annotations

from app.core.prompt_manager import PromptManager


def test_prompt_render_and_sanitization(config_loader) -> None:
    config_loader.load()
    manager = PromptManager(config_loader, prompts_dir="prompts")
    rendered, version = manager.render("faq", "hello {bad}")
    assert version == "v1"
    assert "{{bad}}" in rendered


def test_prompt_activate_version(config_loader) -> None:
    config_loader.load()
    manager = PromptManager(config_loader, prompts_dir="prompts")
    previous, new = manager.activate_version("faq", "v2")
    assert previous == "v1"
    assert new == "v2"
    rendered, _ = manager.render("faq", "test")
    assert "next action" in rendered
    manager.activate_version("faq", "v1")
