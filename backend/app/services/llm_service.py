import asyncio
import json
import re
from typing import Any

import httpx

from app.config import settings
from app.database.models import ToolResult
from app.tools.registry import ToolRegistry


class LLMService:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry
        self.primary_provider = "openai"
        self.fallback_provider = "openrouter"
        self.current_provider = self.primary_provider
        self.current_model = settings.default_model

    def get_current_provider(self) -> str:
        return self.current_provider

    async def switch_provider(self) -> None:
        if self.current_provider == self.primary_provider:
            self.current_provider = self.fallback_provider
            self.current_model = settings.fallback_model
        else:
            self.current_provider = self.primary_provider
            self.current_model = settings.default_model

    async def generate_response(
        self, session_message: str
    ) -> tuple[str, list[str], list[ToolResult], dict[str, int | bool]]:
        usage_summary = {
            "llm_input_tokens": 0,
            "llm_output_tokens": 0,
            "provider_usage_available": False,
        }
        provider_result = await self._provider_initial_response(session_message)
        if provider_result is None:
            answer, used_tools, tool_results = await self._heuristic_generate_response(
                session_message
            )
            return answer, used_tools, tool_results, usage_summary

        initial_content, tool_calls, initial_usage = provider_result
        usage_summary["llm_input_tokens"] += initial_usage[0]
        usage_summary["llm_output_tokens"] += initial_usage[1]
        usage_summary["provider_usage_available"] = True
        if not tool_calls:
            return (
                initial_content or "I can help with weather, calculations, and web search.",
                [],
                [],
                usage_summary,
            )

        tool_results: list[ToolResult] = []
        used_tools: list[str] = []
        for tool_name, params in tool_calls:
            used_tools.append(tool_name)
            tool_results.append(await self.registry.execute_tool(tool_name, params))

        final_response = await self._provider_final_response(
            user_message=session_message,
            tool_calls=tool_calls,
            tool_results=tool_results,
        )
        if final_response is None:
            final_answer = await self._compose_answer(session_message, tool_calls, tool_results)
        else:
            final_answer, final_usage = final_response
            usage_summary["llm_input_tokens"] += final_usage[0]
            usage_summary["llm_output_tokens"] += final_usage[1]
        return final_answer, used_tools, tool_results, usage_summary

    async def stream_text(self, content: str):
        for token in content.split(" "):
            if not token:
                continue
            yield token + " "
            await asyncio.sleep(0.005)

    async def _provider_initial_response(
        self, message: str
    ) -> tuple[str | None, list[tuple[str, dict[str, Any]]], tuple[int, int]] | None:
        if self.current_provider == "openai" and not settings.openai_api_key:
            return None
        if self.current_provider == "openrouter" and not settings.openrouter_api_key:
            return None

        payload = {
            "model": self.current_model,
            "messages": [{"role": "user", "content": message}],
            "tools": self.registry.get_tool_schemas(),
            "tool_choice": "auto",
            "temperature": 0,
            "max_tokens": 100,
        }
        try:
            response_json = await self._chat_completion(payload)
            message_obj = response_json["choices"][0]["message"]
            tool_calls = message_obj.get("tool_calls", [])
            usage = self._extract_usage(response_json)
            parsed: list[tuple[str, dict[str, Any]]] = []
            for call in tool_calls:
                name = call["function"]["name"]
                args = json.loads(call["function"].get("arguments") or "{}")
                if self.registry.has_tool(name):
                    parsed.append((name, args))
            return message_obj.get("content"), parsed, usage
        except Exception:
            # Switch provider once then fall back to heuristic.
            await self.switch_provider()
            try:
                if (
                    self.current_provider == "openrouter"
                    and settings.openrouter_api_key
                ) or (self.current_provider == "openai" and settings.openai_api_key):
                    response_json = await self._chat_completion(payload)
                    message_obj = response_json["choices"][0]["message"]
                    tool_calls = message_obj.get("tool_calls", [])
                    usage = self._extract_usage(response_json)
                    parsed = []
                    for call in tool_calls:
                        name = call["function"]["name"]
                        args = json.loads(call["function"].get("arguments") or "{}")
                        if self.registry.has_tool(name):
                            parsed.append((name, args))
                    return message_obj.get("content"), parsed, usage
            except Exception:
                return None
        return None

    async def _provider_final_response(
        self,
        user_message: str,
        tool_calls: list[tuple[str, dict[str, Any]]],
        tool_results: list[ToolResult],
    ) -> tuple[str, tuple[int, int]] | None:
        if self.current_provider == "openai" and not settings.openai_api_key:
            return None
        if self.current_provider == "openrouter" and not settings.openrouter_api_key:
            return None

        tool_result_lines: list[str] = []
        for (tool_name, params), result in zip(tool_calls, tool_results, strict=False):
            tool_result_lines.append(
                json.dumps(
                    {
                        "tool": tool_name,
                        "arguments": params,
                        "success": result.success,
                        "data": result.data,
                        "error_message": result.error_message,
                    },
                    ensure_ascii=True,
                )
            )
        tool_result_text = "\n".join(tool_result_lines)
        payload = {
            "model": self.current_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a concise assistant. Use provided tool outputs as source of truth. "
                        "If a tool failed, clearly say what failed and suggest the next action."
                    ),
                },
                {"role": "user", "content": user_message},
                {
                    "role": "assistant",
                    "content": (
                        "Tool execution results (JSON lines):\n"
                        f"{tool_result_text}\n"
                        "Generate final response for the user."
                    ),
                },
            ],
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
        }
        try:
            response_json = await self._chat_completion(payload)
            usage = self._extract_usage(response_json)
            return response_json["choices"][0]["message"].get("content"), usage
        except Exception:
            return None

    async def _heuristic_generate_response(
        self, session_message: str
    ) -> tuple[str, list[str], list[ToolResult]]:
        tool_calls = self._heuristic_tool_selection(session_message)
        tool_results: list[ToolResult] = []
        used_tools: list[str] = []
        for tool_name, params in tool_calls:
            used_tools.append(tool_name)
            tool_results.append(await self.registry.execute_tool(tool_name, params))
        answer = await self._compose_answer(session_message, tool_calls, tool_results)
        return answer, used_tools, tool_results

    async def _chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.current_provider == "openai":
            base_url = settings.openai_base_url
            api_key = settings.openai_api_key
            headers = {"Authorization": f"Bearer {api_key}"}
        else:
            base_url = settings.openrouter_base_url
            api_key = settings.openrouter_api_key
            headers = {
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "http://localhost",
                "X-Title": "Multi-Function AI Assistant",
            }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _extract_usage(response_json: dict[str, Any]) -> tuple[int, int]:
        usage = response_json.get("usage") or {}
        input_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0))
        output_tokens = usage.get("completion_tokens", usage.get("output_tokens", 0))
        return int(input_tokens or 0), int(output_tokens or 0)

    def _heuristic_tool_selection(self, message: str) -> list[tuple[str, dict[str, Any]]]:
        text = message.lower().strip()
        tool_calls: list[tuple[str, dict[str, Any]]] = []
        if self._is_weather_intent(text):
            location = re.sub(r"(?i).*(in|at)\s+", "", message).strip(" ?.")
            tool_calls.append(("get_weather", {"location": location or "current location"}))
        if self._is_math_intent(text):
            expr = message.replace("calculate", "").replace("what is", "").strip(" ?.")
            tool_calls.append(("calculate", {"expression": expr}))
        if self._is_search_intent(text):
            query = re.sub(r"(?i)^(search|find|look up)\s+", "", message).strip(" ?.")
            tool_calls.append(("search", {"query": query or message, "num_results": 5}))
        return tool_calls

    @staticmethod
    def _is_weather_intent(text: str) -> bool:
        return any(word in text for word in ["weather", "temperature", "rain", "humidity"])

    @staticmethod
    def _is_math_intent(text: str) -> bool:
        has_math_symbols = bool(re.search(r"[0-9][0-9+\-*/^().= ]+", text))
        keywords = ["calculate", "solve", "integrate", "differentiate", "derivative", "equation"]
        return has_math_symbols or any(keyword in text for keyword in keywords)

    @staticmethod
    def _is_search_intent(text: str) -> bool:
        prompts = ["search", "find", "look up", "latest", "news", "who is", "what is"]
        return any(prompt in text for prompt in prompts)

    async def _compose_answer(
        self,
        message: str,
        tool_calls: list[tuple[str, dict[str, Any]]],
        tool_results: list[ToolResult],
    ) -> str:
        if not tool_calls:
            return (
                "I can help with weather, calculations, and web search. "
                "Ask me a task that needs one of these tools."
            )

        lines = []
        for (tool_name, _), result in zip(tool_calls, tool_results, strict=False):
            if not result.success:
                lines.append(f"{tool_name} failed: {result.error_message}")
                continue

            data = result.data if isinstance(result.data, dict) else {}
            if tool_name == "calculate":
                lines.append(f"Result: {data.get('result', data)}")
            elif tool_name == "get_weather":
                lines.append(
                    "Weather"
                    f" in {data.get('location', 'unknown')}: "
                    f"{data.get('condition', 'N/A')}, "
                    f"{data.get('temperature_c', 'N/A')}C, "
                    f"humidity {data.get('humidity_percent', 'N/A')}%, "
                    f"wind {data.get('wind_speed_mps', 'N/A')} m/s."
                )
            elif tool_name == "search":
                results = data.get("results", [])
                if not results:
                    lines.append("No search results found.")
                else:
                    lines.append("Top search results:")
                    for idx, item in enumerate(results[:3], start=1):
                        title = item.get("title") or "Untitled"
                        url = item.get("url") or "No URL"
                        lines.append(f"{idx}. {title} - {url}")
            else:
                lines.append(str(data) if data else "Tool executed successfully.")
        return "\n".join(lines)
