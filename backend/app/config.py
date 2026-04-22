from pathlib import Path

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Load template first, then let real .env override it.
        env_file=[ROOT_DIR / "config/.env.example", ROOT_DIR / ".env"],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openweather_api_key: str = Field(default="", alias="OPENWEATHER_API_KEY")
    serper_api_key: str = Field(default="", alias="SERPER_API_KEY")

    openai_base_url: str = Field(
        default="https://api.openai.com/v1", alias="OPENAI_BASE_URL"
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL"
    )
    openweather_base_url: str = Field(
        default="https://api.openweathermap.org/data/2.5", alias="OPENWEATHER_BASE_URL"
    )
    serper_base_url: str = Field(default="https://google.serper.dev", alias="SERPER_BASE_URL")

    database_url: str = Field(default="sqlite:///data/assistant.db", alias="DATABASE_URL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    host: str = Field(default="127.0.0.1", alias="HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    frontend_port: int = Field(default=8501, alias="FRONTEND_PORT")

    default_model: str = Field(default="gpt-4o-mini", alias="DEFAULT_MODEL")
    fallback_model: str = Field(default="gpt-4.1-nano", alias="FALLBACK_MODEL")
    max_tokens: int = Field(default=1024, alias="MAX_TOKENS")
    temperature: float = Field(default=0.2, alias="TEMPERATURE")

    @field_validator("default_model", "fallback_model")
    @classmethod
    def validate_allowed_models(cls, value: str) -> str:
        allowed = {"gpt-4.1-nano", "gpt-4o-mini", "o4-mini"}
        if value not in allowed:
            raise ValueError(f"Model '{value}' is not allowed. Allowed models: {sorted(allowed)}")
        return value


settings = Settings()
