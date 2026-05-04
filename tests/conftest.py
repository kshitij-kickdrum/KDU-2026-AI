from __future__ import annotations

from pathlib import Path

import pytest

from src.storage.database import Database


@pytest.fixture
def temp_db(tmp_path: Path) -> Database:
    db = Database(tmp_path / "test.db")
    db.initialize_database()
    return db
