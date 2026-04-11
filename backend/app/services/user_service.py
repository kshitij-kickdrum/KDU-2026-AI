import json
import uuid
from pathlib import Path

from app.core.exceptions import UserNotFound

_PROFILES_PATH = Path(__file__).parent.parent.parent / "data" / "user_profiles.json"

with _PROFILES_PATH.open() as f:
    _profiles: dict = json.load(f)


def _save_profiles() -> None:
    with _PROFILES_PATH.open("w", encoding="utf-8") as f:
        json.dump(_profiles, f, indent=2)


def _derive_style(age: int) -> str:
    return "child" if age <= 12 else "expert"


def get_user_profile(user_id: str) -> dict:
    profile = _profiles.get(user_id)
    if not profile:
        raise UserNotFound(user_id)
    return profile


def create_user(name: str, location: str, age: int) -> dict:
    user_id = f"u_{uuid.uuid4().hex[:8]}"
    style = _derive_style(age)
    profile = {
        "user_id": user_id,
        "name": name,
        "location": location,
        "age": age,
        "timezone": None,
        "preferred_style": style,
    }
    _profiles[user_id] = profile
    _save_profiles()
    return profile
