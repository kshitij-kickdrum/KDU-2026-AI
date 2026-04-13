"""
LangGraph Conditional Routers

Routers are functions that decide which node to visit next based on state.
They enable branching logic in the graph.
"""

from langgraph.graph import END
from app.agent.state import AgentState


def currency_router(state: AgentState) -> str:
    """Route to appropriate currency conversion node based on user preference."""
    currency = state["currency"]
    
    if currency == "INR":
        return "inr_convert_node"
    elif currency == "EUR":
        return "eur_convert_node"
    else:  # USD
        return "tool_decision_node"


def tool_router(state: AgentState) -> str:
    """Route based on whether LLM wants to call a tool."""
    messages = state["messages"]
    last_message = messages[-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "fetch_price_node"
    else:
        return "buy_decision_node"


def buy_router(state: AgentState) -> str:
    """Route to human approval for every agent trade decision."""
    pending_action = state["pending_action"]
    
    if pending_action in ["buy", "sell"]:
        return "human_approval_node"
    return END
