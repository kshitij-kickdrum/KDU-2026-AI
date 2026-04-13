"""
LangGraph Agent State Definition

State is a dictionary passed between all nodes in the graph.
Each node receives state and returns a partial update that gets merged back.
"""

from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class Holding(TypedDict):
    """A single stock holding in the portfolio."""
    symbol: str
    quantity: float
    avg_buy_price: float


class AgentState(TypedDict):
    """
    Complete agent state that flows through the graph.
    
    The `messages` field uses add_messages reducer to append new messages
    instead of replacing the entire list.
    """
    
    # Conversation history (uses add_messages reducer to append)
    messages: Annotated[list[BaseMessage], add_messages]
    user_prompt: str | None
    
    # Portfolio data
    portfolio: list[Holding]
    symbol: str
    portfolio_total_usd: float
    
    # Currency conversion
    currency: Literal["USD", "INR", "EUR"]
    portfolio_total_converted: float | None
    exchange_rate: float | None
    
    # Trading decision
    pending_action: Literal["buy", "sell"]
    action_approved: bool
    
    # Trade history
    trade_log: list[str]
    
    # Error handling
    error: str | None
