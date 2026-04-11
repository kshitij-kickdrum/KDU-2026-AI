from app.agent.style import get_style_prefix
from app.prompts.personalization import build_user_context


def build_system_prompt(profile: dict, style: str | None, intent: str | None = None) -> str:
    user_context = build_user_context(profile)
    style_prefix = get_style_prefix(style)
    intent_block = ""

    if intent == "weather":
        intent_block = (
            "Task instructions:\n"
            "- This is a weather request.\n"
            "- You have access to the get_weather tool.\n"
            "- Always use the get_weather tool instead of guessing weather data.\n"
            "- If the user names a location, use it.\n"
            "- Otherwise, use the location from the user context.\n"
            "- After using the tool, return only a valid JSON object with: "
            "temperature, feels_like, summary, location, advice.\n\n"
        )
    else:
        intent_block = (
            "Task instructions:\n"
            "- This is a general chat request.\n"
            "- Do not call tools unless they are clearly required.\n"
            "- Return only a valid JSON object with: answer, follow_up.\n\n"
        )

    return (
        f"{style_prefix}\n\n"
        f"{user_context}\n"
        "You already know this user. Do not ask for their location or preferences.\n\n"
        f"{intent_block}"
        "Important:\n"
        "- If the user mentions a specific location in their message, use that location.\n"
        "- Otherwise, use the location from the user context above.\n"
        "- Always respond with a valid JSON object. Do not include any text outside the JSON."
    )
