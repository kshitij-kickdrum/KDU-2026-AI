from app.security.output_filter import filter_parsed


def build_response(
    session_id: str,
    parsed: dict,
    model_used: str,
    tool_used: str | None,
    style_applied: str | None,
) -> dict:
    return {
        "session_id": session_id,
        "response": filter_parsed(parsed),
        "model_used": model_used,
        "tool_used": tool_used,
        "style_applied": style_applied,
    }
