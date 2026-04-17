from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=8000)
    session_id: str | None = Field(default=None, max_length=128)
    override_category: Literal["faq", "complaint", "booking"] | None = None
    override_complexity: Literal["low", "medium", "high"] | None = None
