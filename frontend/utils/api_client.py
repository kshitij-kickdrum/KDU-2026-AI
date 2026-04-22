import json
from collections.abc import Generator

import httpx


class APIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.base_url = base_url.rstrip("/")

    def stream_chat(self, message: str, session_id: str) -> Generator[dict, None, None]:
        with httpx.Client(timeout=60) as client:
            with client.stream(
                "POST",
                f"{self.base_url}/chat/stream",
                json={"message": message, "session_id": session_id, "stream": True},
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    payload = line.removeprefix("data: ")
                    try:
                        yield json.loads(payload)
                    except json.JSONDecodeError:
                        continue

    def get_usage_stats(self, session_id: str, detailed: bool = False) -> dict:
        with httpx.Client(timeout=20) as client:
            response = client.get(
                f"{self.base_url}/usage/stats",
                params={"session_id": session_id, "detailed": str(detailed).lower()},
            )
            if response.status_code == 404:
                return {}
            response.raise_for_status()
            return response.json()

    def health(self) -> dict:
        with httpx.Client(timeout=10) as client:
            response = client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()

