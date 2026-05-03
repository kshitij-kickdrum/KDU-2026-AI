"""Shared workflow helpers."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any


def render_template(template: str, **values: str) -> str:
    """Render a task template."""
    return template.format(**values)


def execute_agent(agent: Any, description: str, expected_output: str) -> str:
    """Execute a CrewAI-like or fallback agent."""
    prompt = f"{description}\nExpected output: {expected_output}"
    if hasattr(agent, "execute_task"):
        return str(agent.execute_task(prompt))
    return f"{getattr(agent, 'role', 'Agent')} completed: {prompt}"


def new_execution_id() -> str:
    """Return a new UUID string."""
    return str(uuid.uuid4())


def now_seconds() -> float:
    """Return monotonic time."""
    return time.perf_counter()


def memory_content(value: str) -> str:
    """Serialize memory content as JSON."""
    return json.dumps({"content": value})
