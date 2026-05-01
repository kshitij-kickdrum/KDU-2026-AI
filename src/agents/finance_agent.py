from __future__ import annotations

from src.agents.base_agent import BaseSDKAgent
from src.tools.finance_tools import create_finance_tools
from src.tools.runtime import ToolRuntime
from src.utils.config import AppConfig


class FinanceAgent(BaseSDKAgent):
    def __init__(self, config: AppConfig, runtime: ToolRuntime, session_id: str) -> None:
        super().__init__(
            name="FinanceAgent",
            instructions=config.prompts["finance"],
            model=config.models.finance,
            tools=create_finance_tools(runtime, session_id),
            config=config,
        )
