from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import settings
from app.core.llm import build_chat_model
from app.tools.weather_tool import get_weather

_llm = build_chat_model(
    model=settings.text_model,
    api_key=settings.text_model_api_key,
)

_tools = [get_weather]
_memory = MemorySaver()


def build_agent(system_prompt: str, enable_tools: bool = True):
    return create_agent(
        model=_llm,
        tools=_tools if enable_tools else [],
        system_prompt=system_prompt,
        checkpointer=_memory,
    )


def _flatten_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(part for part in parts if part).strip()
    return str(content).strip()


def extract_agent_output(result: dict) -> tuple[str, str | None]:
    messages = result.get("messages", [])
    tool_used: str | None = None
    final_content = ""

    for message in messages:
        if isinstance(message, AIMessage) and message.tool_calls:
            tool_used = message.tool_calls[-1].get("name", tool_used)
        if isinstance(message, ToolMessage):
            tool_used = message.name or tool_used

    for message in reversed(messages):
        if isinstance(message, AIMessage):
            candidate = _flatten_content(message.content)
            if candidate:
                final_content = candidate
                break

    return final_content, tool_used


def run_agent(agent, message: str, session_id: str) -> tuple[str, str | None]:
    config = {"configurable": {"thread_id": session_id}}
    result = agent.invoke({"messages": [("human", message)]}, config=config)
    return extract_agent_output(result)
