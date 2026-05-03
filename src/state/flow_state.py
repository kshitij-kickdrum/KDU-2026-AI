"""Pydantic state for the event-driven research flow."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class FlowState(BaseModel):
    """Validated state shared by research, fact-checking, and writing."""

    model_config = ConfigDict(validate_assignment=True)

    research_results: str | None = Field(default=None, max_length=10_000)
    fact_check_status: Literal["pending", "passed", "failed"] = "pending"
    fact_check_details: str | None = Field(default=None, max_length=5_000)
    iteration_counter: int = Field(default=0, ge=0, le=3)
    final_output: str | None = Field(default=None, max_length=15_000)
    execution_start_time: datetime = Field(default_factory=utc_now)
    last_updated: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def refresh_last_updated(self) -> "FlowState":
        """Refresh last_updated after validation."""
        object.__setattr__(self, "last_updated", utc_now())
        return self

    def updated(self, **changes: object) -> "FlowState":
        """Return a new state with atomic updates applied."""
        return self.model_copy(update={**changes, "last_updated": utc_now()})
