from fastapi import APIRouter

from app.models.request_models import UserRegistrationRequest
from app.models.response_models import UserRegistrationResponse
from app.services.user_service import create_user, get_user_profile

router = APIRouter()


@router.post("/user/register", status_code=201)
async def register_user(body: UserRegistrationRequest) -> UserRegistrationResponse:
    profile = create_user(name=body.name, location=body.location, age=body.age)
    return UserRegistrationResponse(
        user_id=profile["user_id"],
        name=profile["name"],
        location=profile["location"],
        age=profile["age"],
        style=profile["preferred_style"],
    )


@router.get("/user/{user_id}")
async def get_user(user_id: str) -> dict:
    return get_user_profile(user_id)
