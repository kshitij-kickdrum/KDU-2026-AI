import httpx
from langchain_openai import ChatOpenAI

from app.core.config import settings


def build_chat_model(*, model: str, api_key: str, temperature: float = 0) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=settings.model_max_tokens,
        api_key=api_key,
        base_url=settings.openrouter_base_url,
        use_responses_api=False,
        max_retries=2,
        timeout=30,
        http_client=httpx.Client(trust_env=False),
        http_async_client=httpx.AsyncClient(trust_env=False),
    )
