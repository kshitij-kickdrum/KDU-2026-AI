from fastapi import APIRouter, HTTPException, Query

from app.api.chat import usage_tracker
from app.utils.errors import ValidationError
from app.utils.validators import validate_session_id


router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/stats")
async def usage_stats(
    session_id: str = Query(...), detailed: bool = Query(default=False)
) -> dict:
    try:
        validate_session_id(session_id)
    except ValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    data = usage_tracker.get_session_stats(session_id, detailed=detailed)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    return data

