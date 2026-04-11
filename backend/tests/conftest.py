import pytest
from fastapi.testclient import TestClient

from app.memory.session_memory import (
    _session_index as session_index,
    _session_owner as session_owner,
    _store as memory_store,
)


@pytest.fixture(autouse=True)
def clear_memory():
    """Wipe session memory before every test so tests don't bleed into each other."""
    memory_store.clear()
    session_owner.clear()
    session_index.clear()
    yield
    memory_store.clear()
    session_owner.clear()
    session_index.clear()


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


@pytest.fixture
def mock_profile():
    return {
        "user_id": "u_001",
        "name": "Riya",
        "location": "Mumbai, India",
        "timezone": "Asia/Kolkata",
        "preferred_style": "expert",
    }


@pytest.fixture
def mock_profile_child():
    return {
        "user_id": "u_002",
        "name": "Arjun",
        "location": "Delhi, India",
        "timezone": "Asia/Kolkata",
        "preferred_style": "child",
    }


@pytest.fixture
def chat_payload():
    return {
        "user_id": "u_001",
        "session_id": "sess_test_001",
        "message": "What is the weather today?",
    }
