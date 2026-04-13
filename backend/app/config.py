"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenRouter API (using GPT-4o-mini instead of direct OpenAI)
    openai_api_key: str
    openai_base_url: str = "https://openrouter.ai/api/v1"
    openai_model: str = "openai/gpt-4o-mini"
    
    # LangSmith (automatic tracing of LLM calls, tools, and nodes)
    langchain_api_key: str
    langchain_tracing_v2: bool = True
    langchain_project: str = "stock-trading-agent"
    
    # SQLite checkpoint database for persisting agent state
    checkpoint_db_path: str = "./data/checkpoints.db"
    
    # Fallback exchange rates if API fails
    rate_inr: float = 83.5
    rate_eur: float = 0.92
    
    # External API keys
    freecurrency_api_key: str
    finnhub_api_key: str
    
    # Timeouts
    stock_api_timeout_seconds: int = 10
    
    # Application metadata
    app_version: str = "1.0.0"
    
    # Feature flags
    agent_enabled: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
