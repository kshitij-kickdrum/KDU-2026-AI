from typing import Any

from pydantic import BaseModel, ConfigDict


class UserRegistrationResponse(BaseModel):
    user_id: str
    name: str
    location: str
    age: int
    style: str


class ChatResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    session_id: str
    response: dict[str, Any]
    model_used: str
    tool_used: str | None = None
    style_applied: str | None = None


class HistoryMessage(BaseModel):
    role: str
    content: str


class HistoryResponse(BaseModel):
    session_id: str
    message_count: int
    messages: list[HistoryMessage]


class SessionSummary(BaseModel):
    session_id: str
    title: str
    preview: str
    created_at: int
    updated_at: int
    message_count: int


class SessionListResponse(BaseModel):
    sessions: list[SessionSummary]
