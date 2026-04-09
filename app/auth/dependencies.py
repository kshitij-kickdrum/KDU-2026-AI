import uuid
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_access_token
from app.auth.exceptions import InvalidCredentials, ForbiddenAction
from app.users.models import User
from app.users.service import get_user_by_id
from app.db.session import get_db_session

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise InvalidCredentials()
    except JWTError:
        raise InvalidCredentials()

    return await get_user_by_id(db, uuid.UUID(user_id))


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role.value != "admin":
        raise ForbiddenAction()
    return current_user
