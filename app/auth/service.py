from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password, verify_password, create_access_token
from app.users.models import User
from app.users.service import get_user_by_email
from app.auth.schemas import RegisterRequest, LoginRequest, TokenResponse
from app.auth.exceptions import UserAlreadyExists, InvalidCredentials


async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise UserAlreadyExists()

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def login_user(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    user = await get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise InvalidCredentials()

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(access_token=token)
