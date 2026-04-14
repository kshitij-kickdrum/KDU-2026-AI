"""GET /api/v1/state/{thread_id} Endpoint - Get current state"""

from typing import Annotated

from fastapi import APIRouter, Path

from app.models import StateResponse
from app.agent.graph import graph
from app.main import AppException
from app.session_index import resolve_thread_id


router = APIRouter()


@router.get("/state/{thread_id}", response_model=StateResponse)
async def get_state(thread_id: Annotated[str, Path(description="Thread ID of the agent session")]):
    """Get the current state of an agent session from checkpoint."""
    resolved_thread_id = resolve_thread_id(thread_id) or thread_id
    config = {"configurable": {"thread_id": resolved_thread_id}}
    
    try:
        state_snapshot = graph.get_state(config)
        
        if not state_snapshot or not state_snapshot.values:
            raise AppException(
                code="THREAD_NOT_FOUND",
                message=f"No checkpoint found for session: {thread_id}",
                http_status=404
            )
        
        current_state = state_snapshot.values
        
        # Determine status
        pending_action = current_state.get("pending_action")
        action_approved = bool(current_state.get("action_approved"))

        if pending_action in {"buy", "sell"} and not action_approved:
            status = "awaiting_approval"
        elif not state_snapshot.next:
            status = "completed"
        else:
            status = "in_progress"
        
        return StateResponse(
            thread_id=resolved_thread_id,
            status=status,
            state=current_state
        )
    
    except AppException:
        raise
    except Exception as e:
        raise AppException(
            code="CHECKPOINT_ERROR",
            message=f"Failed to read state: {str(e)}",
            http_status=500
        )
