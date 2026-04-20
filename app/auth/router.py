from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.schemas import RegisterRequest, LoginRequest, TokenResponse
from app.auth.service import register_user, login_user
from app.users.schemas import UserResponse
from app.db.session import get_db_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest, db: AsyncSession = Depends(get_db_session)
) -> UserResponse:
    user = await register_user(db, data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest, db: AsyncSession = Depends(get_db_session)
) -> TokenResponse:
    return await login_user(db, data)
