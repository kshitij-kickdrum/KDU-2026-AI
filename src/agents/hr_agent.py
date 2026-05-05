from __future__ import annotations

from src.agents.base_agent import BaseSDKAgent
from src.tools.hr_tools import create_hr_tools
from src.tools.runtime import ToolRuntime
from src.utils.config import AppConfig


class HRAgent(BaseSDKAgent):
    def __init__(self, config: AppConfig, runtime: ToolRuntime, session_id: str) -> None:
        super().__init__(
            name="HRAgent",
            instructions=config.prompts["hr"],
            model=config.models.hr,
            tools=create_hr_tools(runtime, session_id),
            config=config,
        )
