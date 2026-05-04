"""Workspace-local test paths that do not rely on pytest temp fixtures."""

from __future__ import annotations

import uuid
from pathlib import Path


def make_test_path(name: str) -> Path:
    """Return a unique path under data/test_runs."""
    path = Path.cwd() / "data" / "test_runs" / f"{name}_{uuid.uuid4().hex}"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
