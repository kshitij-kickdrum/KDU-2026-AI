"""
LangGraph Agent Construction

Builds the complete agent graph with nodes, edges, checkpointing, and interrupts.
LangSmith automatically traces all executions when LANGCHAIN_TRACING_V2=true.
"""

import os
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode

from app.agent.state import AgentState
from app.agent.nodes import (
    portfolio_node,
    inr_convert_node,
    eur_convert_node,
    tool_decision_node,
    buy_decision_node,
    human_approval_node,
    execute_trade_node,
)
from app.agent.router import currency_router, tool_router, buy_router
from app.agent.tools import fetch_stock_price
from app.config import settings

# Ensure LangSmith env vars are set at import time
os.environ.setdefault("LANGCHAIN_TRACING_V2", str(settings.langchain_tracing_v2).lower())
os.environ.setdefault("LANGCHAIN_API_KEY", settings.langchain_api_key)
os.environ.setdefault("LANGCHAIN_PROJECT", settings.langchain_project)


def create_graph():
    """
    Build and compile the trading agent graph.
    
    Workflow:
    1. Calculate portfolio value
    2. Convert currency (if needed)
    3. Ask LLM if we need stock price
    4. Fetch stock price (if LLM wants it)
    5. Ask LLM for buy/sell decision
    6. Get human approval (if trade pending)
    7. Execute trade (if approved)
    """
    # Create StateGraph
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("portfolio_node", portfolio_node)
    graph.add_node("inr_convert_node", inr_convert_node)
    graph.add_node("eur_convert_node", eur_convert_node)
    graph.add_node("tool_decision_node", tool_decision_node)
    graph.add_node("fetch_price_node", ToolNode([fetch_stock_price]))
    graph.add_node("buy_decision_node", buy_decision_node)
    graph.add_node("human_approval_node", human_approval_node)
    graph.add_node("execute_trade_node", execute_trade_node)
    
    # Set entry point
    graph.set_entry_point("portfolio_node")
    
    # Add edges
    graph.add_conditional_edges(
        "portfolio_node",
        currency_router,
        {
            "inr_convert_node": "inr_convert_node",
            "eur_convert_node": "eur_convert_node",
            "tool_decision_node": "tool_decision_node",
        }
    )
    
    graph.add_edge("inr_convert_node", "tool_decision_node")
    graph.add_edge("eur_convert_node", "tool_decision_node")
    
    graph.add_conditional_edges(
        "tool_decision_node",
        tool_router,
        {
            "fetch_price_node": "fetch_price_node",
            "buy_decision_node": "buy_decision_node",
        }
    )
    
    graph.add_edge("fetch_price_node", "buy_decision_node")
    
    graph.add_conditional_edges(
        "buy_decision_node",
        buy_router,
        {
            "human_approval_node": "human_approval_node",
            END: END,
        }
    )
    
    graph.add_edge("human_approval_node", "execute_trade_node")
    graph.add_edge("execute_trade_node", END)
    
    # Create checkpointer (newer langgraph-checkpoint-sqlite returns a context manager).
    # Keep the context alive for the process lifetime.
    checkpointer_ctx = SqliteSaver.from_conn_string(settings.checkpoint_db_path)
    checkpointer = checkpointer_ctx.__enter__()
    
    # Compile graph with checkpointing; HITL pause is handled in human_approval_node via interrupt().
    compiled_graph = graph.compile(
        checkpointer=checkpointer,
    )

    # Attach context manager reference so it is not garbage-collected.
    setattr(compiled_graph, "_checkpointer_ctx", checkpointer_ctx)
    
    return compiled_graph


graph = create_graph()
