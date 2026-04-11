def build_user_context(profile: dict) -> str:
    lines = [
        "User context:",
        f"- Name: {profile['name']}",
        f"- Location: {profile['location']}",
    ]
    if profile.get("timezone"):
        lines.append(f"- Timezone: {profile['timezone']}")
    return "\n".join(lines) + "\n"
