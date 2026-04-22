import time
from typing import Any

import httpx

from app.config import settings
from app.database.models import ToolResult
from app.tools.base import BaseTool


class WeatherTool(BaseTool):
    name = "get_weather"

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": "Get current weather information for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name, coordinates, or address",
                        }
                    },
                    "required": ["location"],
                },
            },
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()
        location = str(kwargs.get("location", "")).strip()
        if not location:
            return ToolResult(success=False, data=None, error_message="location is required")
        if not settings.openweather_api_key:
            return ToolResult(
                success=False,
                data=None,
                error_message="OpenWeather API key is not configured",
            )

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    f"{settings.openweather_base_url}/weather",
                    params={"q": location, "appid": settings.openweather_api_key, "units": "metric"},
                )
            if response.status_code != 200:
                return ToolResult(
                    success=False,
                    data=None,
                    error_message=f"Weather API error {response.status_code}: {response.text[:120]}",
                    execution_time=time.perf_counter() - started,
                )
            payload = response.json()
            data = {
                "location": f"{payload.get('name')}, {payload.get('sys', {}).get('country', '')}".strip(", "),
                "temperature_c": payload.get("main", {}).get("temp"),
                "humidity_percent": payload.get("main", {}).get("humidity"),
                "wind_speed_mps": payload.get("wind", {}).get("speed"),
                "condition": (payload.get("weather") or [{}])[0].get("description"),
            }
            return ToolResult(
                success=True,
                data=data,
                execution_time=time.perf_counter() - started,
            )
        except httpx.HTTPError as exc:
            return ToolResult(
                success=False,
                data=None,
                error_message=f"Weather request failed: {exc}",
                execution_time=time.perf_counter() - started,
            )

