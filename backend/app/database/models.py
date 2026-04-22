from dataclasses import dataclass
from typing import Any


USAGE_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    request_type TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    tool_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER NOT NULL,
    estimated_cost REAL NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    tools_used TEXT,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT
);
"""

SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_requests INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0.0
);
"""

TOOL_USAGE_TABLE = """
CREATE TABLE IF NOT EXISTS tool_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    execution_time REAL NOT NULL,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
"""


@dataclass(slots=True)
class ToolResult:
    success: bool
    data: Any
    error_message: str | None = None
    execution_time: float = 0.0

