from __future__ import annotations

import json
import logging
import time
from typing import Any

from src.agents.sdk import build_openrouter_model, load_agents_sdk
from src.core.exceptions import (
    AgentExecutionError,
    MissingAPIKeyError,
    ProviderConnectionError,
    TokenBudgetError,
)
from src.utils.config import AppConfig
from src.utils.token_counter import TokenCounter

LOGGER = logging.getLogger(__name__)


class BaseSDKAgent:
    def __init__(
        self,
        *,
        name: str,
        instructions: str,
        model: str,
        tools: list[Any],
        config: AppConfig,
    ) -> None:
        self.name = name
        self.instructions = instructions
        self.model = model
        self.tools = tools
        self.config = config
        self.counter = TokenCounter(model)
        self._configure_sdk_key()
        agent_cls, _, _, model_settings_cls = load_agents_sdk()
        self.sdk_agent = agent_cls(
            name=name,
            instructions=instructions,
            model=model,
            tools=tools,
            model_settings=model_settings_cls(
                max_tokens=config.budgets.max_output_tokens,
                truncation="disabled",
            ),
        )

    def run(self, query: str, context: dict[str, Any] | None = None) -> str:
        if not self.config.openai_api_key:
            raise MissingAPIKeyError(
                "OPENAI_API_KEY is not configured. Create a .env file from .env.example "
                "and set OPENAI_API_KEY before running live Agents SDK calls."
            )
        input_payload = self._build_input(query, context)
        input_tokens = self.counter.count_payload(input_payload)
        if input_tokens > self.config.budgets.max_input_tokens:
            raise TokenBudgetError(
                f"{self.name} input has {input_tokens} tokens; "
                f"limit is {self.config.budgets.max_input_tokens}."
            )

        last_error: Exception | None = None
        for attempt in range(self.config.rate_limits.max_retries + 1):
            try:
                return self._run_once(input_payload, input_tokens)
            except Exception as exc:
                last_error = exc
                if not self._looks_retryable(exc) or attempt >= self.config.rate_limits.max_retries:
                    break
                delay = min(
                    self.config.rate_limits.backoff_base_seconds * (2**attempt),
                    self.config.rate_limits.backoff_max_seconds,
                )
                LOGGER.warning(
                    "Retrying %s after retryable SDK error: attempt=%s delay=%s error=%s",
                    self.name,
                    attempt + 1,
                    delay,
                    exc,
                )
                time.sleep(delay)

        if self.config.openrouter_api_key:
            try:
                return self._run_once(input_payload, input_tokens, use_openrouter=True)
            except Exception as fallback_error:
                last_error = fallback_error

        if last_error and self._looks_connection_error(last_error):
            raise ProviderConnectionError(
                f"{self.name} could not reach the configured LLM provider. "
                "Check your internet connection, proxy/VPN settings, and API provider availability."
            ) from last_error
        raise AgentExecutionError(f"{self.name} failed: {last_error}") from last_error

    def _run_once(
        self,
        input_payload: str,
        input_tokens: int,
        *,
        use_openrouter: bool = False,
    ) -> str:
        _, runner_cls, _, _ = load_agents_sdk()
        agent = self.sdk_agent
        if use_openrouter:
            LOGGER.warning("Using OpenRouter fallback for agent=%s model=%s", self.name, self.model)
            agent_cls, _, _, model_settings_cls = load_agents_sdk()
            agent = agent_cls(
                name=self.name,
                instructions=self.instructions,
                model=build_openrouter_model(self.model, self.config.openrouter_api_key or ""),
                tools=self.tools,
                model_settings=model_settings_cls(max_tokens=self.config.budgets.max_output_tokens),
            )
        LOGGER.info("Starting SDK run: agent=%s model=%s", self.name, self.model)
        result = runner_cls.run_sync(
            agent,
            input_payload,
            max_turns=self.config.budgets.max_agent_turns,
        )
        output = str(getattr(result, "final_output", ""))
        LOGGER.info(
            "Token usage: agent=%s model=%s input_tokens_estimate=%s output_tokens_estimate=%s",
            self.name,
            self.model,
            input_tokens,
            self.counter.count_text(output),
        )
        return output

    def _build_input(self, query: str, context: dict[str, Any] | None) -> str:
        if not context:
            return query
        return (
            f"Task:\n{query}\n\n"
            "Structured context payload, not full chat history:\n"
            f"{json.dumps(context, ensure_ascii=False, default=str)}"
        )

    @staticmethod
    def _looks_retryable(error: Exception) -> bool:
        text = str(error).lower()
        return any(
            marker in text
            for marker in ["rate limit", "429", "timeout", "temporarily", "connection error"]
        )

    @staticmethod
    def _looks_connection_error(error: Exception) -> bool:
        text = str(error).lower()
        return any(
            marker in text
            for marker in [
                "connection error",
                "connection refused",
                "all connection attempts failed",
                "api connection",
            ]
        )

    def _configure_sdk_key(self) -> None:
        if not self.config.openai_api_key:
            return
        try:
            import agents

            client = agents.AsyncOpenAI(
                api_key=self.config.openai_api_key,
                timeout=15.0,
                max_retries=0,
            )
            agents.set_tracing_disabled(True)
            agents.set_default_openai_client(client, use_for_tracing=False)
        except Exception:
            LOGGER.debug("Could not configure default OpenAI key for Agents SDK", exc_info=True)
