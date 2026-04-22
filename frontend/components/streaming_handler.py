from dataclasses import dataclass, field

import streamlit as st


@dataclass
class StreamState:
    content: str = ""
    tools: dict[str, str] = field(default_factory=dict)
    usage: dict = field(default_factory=dict)


class StreamingHandler:
    def __init__(self, placeholder, status_placeholder) -> None:
        self.placeholder = placeholder
        self.status_placeholder = status_placeholder
        self.state = StreamState()

    def handle_event(self, event: dict) -> None:
        event_type = event.get("type")
        data = event.get("data", {})

        if event_type == "content":
            self.state.content += data
            self.placeholder.markdown(self.state.content)
        elif event_type == "tool_status":
            tool = data.get("tool", "tool")
            status = data.get("status", "unknown")
            self.state.tools[tool] = status
            self._render_status()
        elif event_type == "tool_result":
            tool = data.get("tool", "tool")
            self.state.tools[tool] = "done" if data.get("success") else "failed"
            self._render_status()
        elif event_type == "usage_update":
            self.state.usage = data
            st.session_state.latest_usage = data

    def _render_status(self) -> None:
        if not self.state.tools:
            return
        lines = [f"- `{tool}`: {status}" for tool, status in self.state.tools.items()]
        self.status_placeholder.markdown("**Tool Status**\n" + "\n".join(lines))

