"""POST /api/v1/run Endpoint - Start agent run"""

from fastapi import APIRouter
from langchain_core.messages import HumanMessage

from app.models import RunRequest, RunResponse
from app.agent.graph import graph
from app.agent.state import Holding
from app.config import settings
from app.main import AppException
from app.session_index import get_or_create_session_ref, upsert_session


router = APIRouter()


@router.post("/run", response_model=RunResponse)
async def run_agent(request: RunRequest):
    """
    Start a new agent run.
    
    Returns HTTP 200 if run completes, HTTP 202 if interrupted (awaiting approval).
    """
    # Check feature flag
    if not settings.agent_enabled:
        raise AppException(
            code="SERVICE_UNAVAILABLE",
            message="Agent is currently disabled",
            http_status=503
        )
    
    # Sanitize symbol input
    symbol = request.symbol
    special_tokens = ["<|endoftext|>", "<|im_start|>", "<|im_end|>", "<|system|>", "<|user|>", "<|assistant|>"]
    for token in special_tokens:
        symbol = symbol.replace(token, "")
    
    # Convert to AgentState format
    portfolio = [
        Holding(
            symbol=h.symbol,
            quantity=h.quantity,
            avg_buy_price=h.avg_buy_price
        )
        for h in request.portfolio
    ]
    
    user_prompt = (request.prompt or "").strip() or (
        f"Analyze {symbol} and decide whether we should BUY or SELL based on current state."
    )

    get_or_create_session_ref(request.thread_id)

    # Create initial state
    initial_state = {
        "messages": [HumanMessage(content=user_prompt)],
        "user_prompt": user_prompt,
        "portfolio": portfolio,
        "portfolio_total_usd": 0.0,
        "currency": request.currency,
        "portfolio_total_converted": None,
        "exchange_rate": None,
        "pending_action": "buy",
        "action_approved": False,
        "trade_log": [],
        "error": None,
        "symbol": symbol,
    }
    
    # Create config with thread_id for checkpointing
    config = {"configurable": {"thread_id": request.thread_id}}
    
    try:
        # Invoke graph
        final_state = graph.invoke(initial_state, config)

        state_snapshot = graph.get_state(config)
        current_state = state_snapshot.values if state_snapshot and state_snapshot.values else final_state

        pending_action = current_state.get("pending_action")
        action_approved = bool(current_state.get("action_approved"))

        # If graph paused before approval, surface that explicitly.
        if pending_action in {"buy", "sell"} and not action_approved:
            upsert_session(
                thread_id=request.thread_id,
                status="awaiting_approval",
                state=current_state,
            )
            return RunResponse(
                status="awaiting_approval",
                thread_id=request.thread_id,
                pending_action=pending_action
            )
        
        # Run completed
        upsert_session(
            thread_id=request.thread_id,
            status="completed",
            state=final_state,
        )
        return RunResponse(
            status="completed",
            thread_id=request.thread_id,
            portfolio_total_usd=final_state["portfolio_total_usd"],
            portfolio_total_converted=final_state.get("portfolio_total_converted"),
            currency=request.currency,
            trade_log=final_state["trade_log"],
            pending_action=final_state.get("pending_action")
        )
    
    except Exception as e:
        # Check if interrupted (HITL)
        if "interrupt" in str(e).lower():
            state_snapshot = graph.get_state(config)
            current_state = state_snapshot.values

            upsert_session(
                thread_id=request.thread_id,
                status="awaiting_approval",
                state=current_state,
            )
            
            return RunResponse(
                status="awaiting_approval",
                thread_id=request.thread_id,
                pending_action=current_state["pending_action"]
            )
        else:
            raise AppException(
                code="AGENT_ERROR",
                message=f"Agent execution failed: {str(e)}",
                http_status=500
            )
