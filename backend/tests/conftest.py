from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from app.core.config_loader import ConfigLoader


@pytest.fixture
def config_loader() -> ConfigLoader:
    return ConfigLoader(config_dir="config", prompts_dir="prompts")


@pytest.fixture
def workspace_tmp_dir() -> Path:
    base = Path("tests/.tmp")
    base.mkdir(parents=True, exist_ok=True)
    target = base / str(uuid4())
    target.mkdir(parents=True, exist_ok=True)
    return target


@pytest.fixture
def temp_db_path(workspace_tmp_dir: Path) -> str:
    return str(workspace_tmp_dir / "test.db")
