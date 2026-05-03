"""Build agents from YAML configuration."""

from __future__ import annotations

from typing import Any

try:
    from crewai_tools import SerperDevTool
except Exception:  # pragma: no cover
    SerperDevTool = None  # type: ignore[assignment]

from src.tools.failing_tool import UnreliableResearchTool
from src.tools.retry import with_exponential_backoff


class RetryWrappedTool:
    """Apply exponential backoff around UnreliableResearchTool."""

    name = "retry_wrapped_unreliable_research_tool"
    description = "Retries the unreliable research tool before degrading."

    def __init__(self) -> None:
        """Create the underlying unreliable tool."""
        self.tool = UnreliableResearchTool()

    def _run(self, query: str) -> str:
        """Run the underlying tool with retries."""
        result = with_exponential_backoff(lambda: self.tool._run(query))
        return result or "Supplemental data unavailable after retries."


class SimpleAgent:
    """Project agent adapter used by workflows and Streamlit.

    CrewAI Agent validation varies across installed versions and can reject
    LangChain chat models or custom tool adapters. This lightweight adapter keeps
    YAML-configured roles/goals/backstories and invokes the configured LLM
    directly when possible.
    """

    def __init__(
        self,
        key: str,
        role: str,
        goal: str,
        backstory: str,
        tools: list[Any],
        llm: Any,
        memory: bool = True,
    ) -> None:
        """Store agent metadata."""
        self.key = key
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.tools = tools
        self.llm = llm
        self.memory = memory

    def _tool_context(self, task: str) -> str:
        """Run safe supplemental tools and return context for the prompt."""
        if self.key != "researcher":
            return ""
        snippets = []
        query = task[:500]
        for tool in self.tools:
            if isinstance(tool, RetryWrappedTool):
                snippets.append(tool._run(query))
        if not snippets:
            return ""
        return "\nSupplemental tool context:\n" + "\n".join(snippets)

    def _build_prompt(self, task: str) -> str:
        """Build the LLM prompt from YAML-configured agent fields."""
        return (
            f"Role: {self.role}\n"
            f"Goal: {self.goal}\n"
            f"Backstory: {self.backstory}\n\n"
            f"Task:\n{task}"
            f"{self._tool_context(task)}"
        )

    @staticmethod
    def _response_text(response: Any) -> str:
        """Extract text from a LangChain response or plain value."""
        content = getattr(response, "content", None)
        if content is not None:
            return str(content)
        return str(response)

    def execute_task(self, task: str) -> str:
        """Execute through a deterministic test LLM or configured chat model."""
        if hasattr(self.llm, "invoke_for_role"):
            return str(self.llm.invoke_for_role(self.key, task))
        prompt = self._build_prompt(task)
        if hasattr(self.llm, "invoke"):
            return self._response_text(self.llm.invoke(prompt))
        return f"{self.role} completed: {prompt}"


def _tool_from_name(name: str) -> Any | None:
    if name == "serper_tool" and SerperDevTool is not None:
        return SerperDevTool()
    if name == "failing_tool":
        return RetryWrappedTool()
    return None


def build_agents(agents_config: dict[str, Any], llm: Any) -> dict[str, Any]:
    """Construct researcher, fact_checker, and writer agents."""
    agents: dict[str, Any] = {}
    for key in ("researcher", "fact_checker", "writer"):
        config = agents_config[key]
        tools = [
            tool
            for tool in (_tool_from_name(name) for name in config.get("tools", []))
            if tool is not None
        ]
        agents[key] = SimpleAgent(
            key,
            config["role"],
            config["goal"],
            config["backstory"],
            tools,
            llm,
            memory=True,
        )
    return agents
