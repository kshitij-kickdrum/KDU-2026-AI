import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.users.models import User
from app.users.exceptions import UserNotFound


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise UserNotFound()
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_all_users(db: AsyncSession, limit: int, offset: int) -> tuple[list[User], int]:
    total_result = await db.execute(select(func.count()).select_from(User))
    total = total_result.scalar()

    result = await db.execute(select(User).limit(limit).offset(offset))
    users = result.scalars().all()
    return list(users), total
