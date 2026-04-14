"""POST /api/v1/approve Endpoint - Resume interrupted run"""

from fastapi import APIRouter

from app.models import ApproveRequest, ApproveResponse
from app.agent.graph import graph
from app.main import AppException
from app.session_index import upsert_session


router = APIRouter()


@router.post("/approve", response_model=ApproveResponse)
async def approve_trade(request: ApproveRequest):
    """
    Resume an interrupted agent run with human approval/rejection.
    Loads state from checkpoint, updates action_approved, and resumes execution.
    """
    config = {"configurable": {"thread_id": request.thread_id}}
    
    try:
        # Check if thread exists
        state_snapshot = graph.get_state(config)
        if not state_snapshot or not state_snapshot.values:
            raise AppException(
                code="THREAD_NOT_FOUND",
                message=f"No checkpoint found for thread_id: {request.thread_id}",
                http_status=404
            )
        
        # Check if already completed
        if not state_snapshot.next:
            raise AppException(
                code="THREAD_ALREADY_COMPLETED",
                message="This thread has already completed. Start a new run.",
                http_status=400
            )
        
        # Update state with approval decision
        state_update = {"action_approved": request.approved}
        graph.update_state(config, state_update)
        
        # Resume graph from checkpointed node
        final_state = graph.invoke(None, config)
        
        status = "completed" if request.approved else "cancelled"

        upsert_session(
            thread_id=request.thread_id,
            status="completed",
            state=final_state,
            cancelled=not request.approved,
        )
        
        return ApproveResponse(
            status=status,
            thread_id=request.thread_id,
            trade_log=final_state["trade_log"],
            portfolio=final_state.get("portfolio"),
            portfolio_total_usd=final_state.get("portfolio_total_usd"),
            portfolio_total_converted=final_state.get("portfolio_total_converted"),
            currency=final_state.get("currency"),
        )
    
    except AppException:
        raise
    except Exception as e:
        raise AppException(
            code="AGENT_ERROR",
            message=f"Failed to resume agent: {str(e)}",
            http_status=500
        )
