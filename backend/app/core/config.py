from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenRouter
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    text_model_api_key: str
    vision_model_api_key: str
    classifier_model_api_key: str

    # Model names
    text_model: str = "openai/gpt-4.1-mini"
    vision_model: str = "openai/gpt-4.1-mini"
    classifier_model: str = "openai/gpt-4.1-mini"
    model_max_tokens: int = 2048

    # Weather
    weather_api_key: str = ""
    use_mock_weather: bool = True

    # App
    log_level: str = "DEBUG"
    environment: str = "development"
    cors_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://[::1]:5173"
    enable_rate_limiting: bool = False
    chat_rate_limit: str = "30/minute"
    image_rate_limit: str = "30/minute"
    use_mock_model_fallbacks: bool = True

    # Agent
    max_parser_retries: int = 2
    max_agent_iterations: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
