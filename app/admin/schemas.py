import uuid
from pydantic import BaseModel, ConfigDict
from app.users.models import UserRole


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole


class AdminUserListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[AdminUserResponse]
