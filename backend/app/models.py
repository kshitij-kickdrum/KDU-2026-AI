"""Pydantic models for FastAPI request/response validation."""

from pydantic import BaseModel, Field
from typing import Literal


class HoldingModel(BaseModel):
    """A single stock holding."""
    symbol: str = Field(..., description="Stock ticker symbol (e.g., 'AAPL')")
    quantity: float = Field(..., gt=0, description="Number of shares owned")
    avg_buy_price: float = Field(..., gt=0, description="Average price paid per share")


class RunRequest(BaseModel):
    """Request body for POST /api/v1/run"""
    thread_id: str = Field(..., description="Unique ID for this agent session")
    portfolio: list[HoldingModel] = Field(..., min_length=1, description="List of stock holdings")
    currency: Literal["USD", "INR", "EUR"] = Field(..., description="Preferred currency for portfolio value")
    symbol: str = Field(..., description="Stock symbol to evaluate for trading")
    prompt: str | None = Field(None, description="Optional custom prompt for the LLM")


class RunResponse(BaseModel):
    """Response body for POST /api/v1/run"""
    status: Literal["completed", "awaiting_approval"]
    thread_id: str
    portfolio_total_usd: float | None = None
    portfolio_total_converted: float | None = None
    currency: str | None = None
    trade_log: list[str] | None = None
    pending_action: Literal["buy", "sell"] | None = None


class ApproveRequest(BaseModel):
    """Request body for POST /api/v1/approve"""
    thread_id: str = Field(..., description="Thread ID of the interrupted run")
    approved: bool = Field(..., description="True to execute trade, False to cancel")


class ApproveResponse(BaseModel):
    """Response body for POST /api/v1/approve"""
    status: Literal["completed", "cancelled"]
    thread_id: str
    trade_log: list[str]
    portfolio: list[HoldingModel] | None = None
    portfolio_total_usd: float | None = None
    portfolio_total_converted: float | None = None
    currency: Literal["USD", "INR", "EUR"] | None = None


class StateResponse(BaseModel):
    """Response body for GET /api/v1/state/{thread_id}"""
    thread_id: str
    status: str
    state: dict


class SessionSummary(BaseModel):
    """Summary for one discovered session without exposing raw thread ID."""
    session_ref: str
    status: Literal["completed", "awaiting_approval", "in_progress", "cancelled"]
    updated_at: str
    portfolio_total_usd: float | None = None
    portfolio_total_converted: float | None = None
    currency: Literal["USD", "INR", "EUR"] | None = None


class SessionsResponse(BaseModel):
    """Response body for GET /api/v1/sessions"""
    sessions: list[SessionSummary]


class SessionStateResponse(BaseModel):
    """Response body for GET /api/v1/sessions/{session_ref}"""
    session_ref: str
    status: Literal["completed", "awaiting_approval", "in_progress", "cancelled"]
    state: dict


class HealthResponse(BaseModel):
    """Response body for GET /api/v1/health"""
    status: Literal["ok"]
    version: str


class ErrorResponse(BaseModel):
    """Standard error response for all 4xx/5xx errors"""
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
