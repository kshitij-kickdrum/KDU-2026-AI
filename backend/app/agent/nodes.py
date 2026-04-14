"""
LangGraph Node Functions

Nodes are functions that take state and return a partial update.
The returned dict is merged back into the full state by LangGraph.
"""

from datetime import datetime
import json
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.types import interrupt

from app.agent.state import AgentState
from app.agent.tools import fetch_stock_price, fetch_live_exchange_rate
from app.config import settings


def _normalize_message_content(content):
    """Parse JSON string payloads into Python values when possible."""
    if not isinstance(content, str):
        return content

    raw = content.strip()
    if not raw:
        return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _extract_price_from_content(content) -> float | None:
    """Extract price from a dict/list payload."""
    if isinstance(content, dict):
        value = content.get("price")
        if isinstance(value, (int, float)) and float(value) > 0:
            return float(value)
        return None

    if isinstance(content, list):
        for item in reversed(content):
            price = _extract_price_from_content(item)
            if price is not None:
                return price

    return None


def _extract_latest_price(messages: list) -> float | None:
    """Return the most recent valid tool-derived price from message history."""
    for message in reversed(messages):
        content = _normalize_message_content(getattr(message, "content", None))
        price = _extract_price_from_content(content)
        if price is not None:
            return price

    return None


def _make_llm(max_tokens: int) -> ChatOpenAI:
    """Create a ChatOpenAI instance configured with OpenRouter."""
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        max_tokens=max_tokens,
    )


def portfolio_node(state: AgentState) -> dict:
    """Calculate total portfolio value in USD."""
    portfolio = state["portfolio"]
    
    if not portfolio:
        return {"portfolio_total_usd": 0.0}
    
    total = sum(
        holding["quantity"] * holding["avg_buy_price"]
        for holding in portfolio
    )
    
    return {"portfolio_total_usd": total}



def inr_convert_node(state: AgentState) -> dict:
    """Convert portfolio value from USD to INR."""
    # Try live rate, fall back to config if API fails
    live_rate = fetch_live_exchange_rate("INR")
    rate = live_rate if live_rate is not None else settings.rate_inr
    
    portfolio_total_usd = state["portfolio_total_usd"]
    converted = portfolio_total_usd * rate
    
    return {
        "portfolio_total_converted": converted,
        "exchange_rate": rate
    }


def eur_convert_node(state: AgentState) -> dict:
    """Convert portfolio value from USD to EUR."""
    # Try live rate, fall back to config if API fails
    live_rate = fetch_live_exchange_rate("EUR")
    rate = live_rate if live_rate is not None else settings.rate_eur
    
    portfolio_total_usd = state["portfolio_total_usd"]
    converted = portfolio_total_usd * rate
    
    return {
        "portfolio_total_converted": converted,
        "exchange_rate": rate
    }



def tool_decision_node(state: AgentState) -> dict:
    """
    Ask LLM whether to fetch current stock price.
    Binds fetch_stock_price tool so LLM can decide to call it.
    """
    llm = _make_llm(max_tokens=500)
    llm_with_tools = llm.bind_tools([fetch_stock_price])
    
    # Get symbol and sanitize input
    symbol = state.get("symbol", "UNKNOWN")
    special_tokens = ["<|endoftext|>", "<|im_start|>", "<|im_end|>", "<|system|>", "<|user|>", "<|assistant|>"]
    for token in special_tokens:
        symbol = symbol.replace(token, "")
    
    prompt = f"Should we fetch the current price for {symbol}? If yes, use the fetch_stock_price tool."
    message = HumanMessage(content=prompt)
    response = llm_with_tools.invoke([message])
    
    return {"messages": [response]}



def buy_decision_node(state: AgentState) -> dict:
    """
    Ask LLM to decide BUY or SELL based on available state.
    """
    llm = _make_llm(max_tokens=120)

    symbol = state.get("symbol", "UNKNOWN")
    currency = state.get("currency", "USD")
    portfolio_total_usd = state.get("portfolio_total_usd", 0.0)
    portfolio_total_converted = state.get("portfolio_total_converted")
    user_prompt = state.get("user_prompt") or ""

    context = (
        "You are a trading agent. Decide exactly one action: BUY or SELL. "
        "Do not return any other token.\n"
        f"User prompt: {user_prompt}\n"
        f"Primary symbol: {symbol}\n"
        f"Execution currency: {currency}\n"
        f"Portfolio total USD: {portfolio_total_usd}\n"
        f"Portfolio total converted: {portfolio_total_converted}\n"
        "Output strictly one word: BUY or SELL."
    )

    response = llm.invoke([HumanMessage(content=context)])
    decision_text = str(response.content).upper()
    action = "sell" if "SELL" in decision_text and "BUY" not in decision_text else "buy"

    decision_message = AIMessage(content=action.upper())
    return {
        "pending_action": action,
        "messages": [decision_message],
    }



def human_approval_node(state: AgentState) -> dict:
    """
    Check if human approved the trade. If not, pause execution.
    Raises interrupt() to pause graph and save checkpoint.
    """
    if not state["action_approved"]:
        interrupt("Awaiting human approval")
    
    return {}


def execute_trade_node(state: AgentState) -> dict:
    """
    Execute the approved trade and log it.
    This is a simulated trade - not calling a real brokerage API.
    """
    action = state["pending_action"]
    symbol = state.get("symbol", "UNKNOWN")
    quantity = 10
    price = _extract_latest_price(state.get("messages", [])) or 150.0
    
    timestamp = datetime.now().isoformat()
    trade_record = f"{timestamp} - {action.upper()} {quantity} shares of {symbol} at ${price:.2f}"
    
    portfolio = [dict(holding) for holding in state.get("portfolio", [])]
    target = next(
        (
            holding
            for holding in portfolio
            if str(holding.get("symbol", "")).upper() == symbol.upper()
        ),
        None,
    )

    if action == "buy":
        if target:
            old_qty = float(target.get("quantity", 0.0))
            old_avg = float(target.get("avg_buy_price", 0.0))
            new_qty = old_qty + quantity
            weighted_avg = ((old_qty * old_avg) + (quantity * price)) / new_qty if new_qty > 0 else price
            target["quantity"] = new_qty
            target["avg_buy_price"] = weighted_avg
        else:
            portfolio.append(
                {
                    "symbol": symbol.upper(),
                    "quantity": float(quantity),
                    "avg_buy_price": float(price),
                }
            )
    elif action == "sell" and target:
        old_qty = float(target.get("quantity", 0.0))
        remaining = max(0.0, old_qty - quantity)
        if remaining > 0:
            target["quantity"] = remaining
        else:
            portfolio = [holding for holding in portfolio if holding is not target]

    portfolio_total_usd = sum(
        float(holding.get("quantity", 0.0)) * float(holding.get("avg_buy_price", 0.0))
        for holding in portfolio
    )

    currency = state.get("currency", "USD")
    exchange_rate = state.get("exchange_rate")
    converted_total = None
    if currency in {"INR", "EUR"} and isinstance(exchange_rate, (int, float)):
        converted_total = portfolio_total_usd * float(exchange_rate)

    new_trade_log = state["trade_log"] + [trade_record]

    return {
        "trade_log": new_trade_log,
        "portfolio": portfolio,
        "portfolio_total_usd": portfolio_total_usd,
        "portfolio_total_converted": converted_total,
    }
