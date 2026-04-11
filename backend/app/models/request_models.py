from typing import Literal

from pydantic import BaseModel, field_validator


class UserRegistrationRequest(BaseModel):
    name: str
    location: str
    age: int

    @field_validator("name")
    @classmethod
    def name_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2 or len(v) > 50:
            raise ValueError("name must be between 2 and 50 characters")
        return v

    @field_validator("location")
    @classmethod
    def location_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2 or len(v) > 100:
            raise ValueError("location must be between 2 and 100 characters")
        return v

    @field_validator("age")
    @classmethod
    def age_valid(cls, v: int) -> int:
        if v < 5 or v > 120:
            raise ValueError("age must be between 5 and 120")
        return v


class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str
    style: Literal["expert", "child"] | None = None

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message cannot be blank")
        if len(v) > 2000:
            raise ValueError("message exceeds maximum length of 2000 characters")
        return v


class SessionRequest(BaseModel):
    user_id: str
    session_id: str
