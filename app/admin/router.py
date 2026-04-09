from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import require_admin
from app.users.models import User
from app.users.service import get_all_users
from app.admin.schemas import AdminUserListResponse, AdminUserResponse
from app.db.session import get_db_session

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> AdminUserListResponse:
    users, total = await get_all_users(db, limit, offset)
    return AdminUserListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[AdminUserResponse.model_validate(u) for u in users],
    )
