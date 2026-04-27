from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_base_url: str
    openrouter_site_url: str
    openrouter_app_name: str
    app_env: str
    log_level: str
    max_file_size_mb: int
    data_dir: Path
    uploads_dir: Path
    transcripts_dir: Path
    vector_store_dir: Path
    database_path: Path
    whisper_model: str
    whisper_device: str
    embedding_batch_size: int
    max_retries: int
    retry_base_delay: int
    vision_model: str
    pdf_render_scale: float
    pdf_page_max_tokens: int
    pdf_max_pages: int
    summary_model: str
    embedding_model: str


def _required_env(key: str) -> str:
    value = os.getenv(key, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


def get_settings(validate_openai_key: bool = False) -> Settings:
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if validate_openai_key and not openai_api_key:
        raise ValueError("OPENAI_API_KEY is required")

    data_dir = Path(os.getenv("DATA_DIR", "data"))
    uploads_dir = Path(os.getenv("UPLOADS_DIR", str(data_dir / "uploads")))
    transcripts_dir = Path(os.getenv("TRANSCRIPTS_DIR", str(data_dir / "transcripts")))
    vector_store_dir = Path(os.getenv("VECTOR_STORE_DIR", str(data_dir / "vector_store")))
    database_path = Path(os.getenv("DATABASE_PATH", str(data_dir / "app.db")))

    settings = Settings(
        openai_api_key=openai_api_key,
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip(),
        openrouter_site_url=os.getenv("OPENROUTER_SITE_URL", "").strip(),
        openrouter_app_name=os.getenv("OPENROUTER_APP_NAME", "Content Accessibility Platform").strip(),
        app_env=os.getenv("APP_ENV", "development"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "100")),
        data_dir=data_dir,
        uploads_dir=uploads_dir,
        transcripts_dir=transcripts_dir,
        vector_store_dir=vector_store_dir,
        database_path=database_path,
        whisper_model=os.getenv("WHISPER_MODEL", "openai/whisper-small"),
        whisper_device=os.getenv("WHISPER_DEVICE", "auto"),
        embedding_batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", "100")),
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        retry_base_delay=int(os.getenv("RETRY_BASE_DELAY", "2")),
        vision_model=os.getenv("VISION_MODEL", "gpt-4o-mini").strip(),
        pdf_render_scale=float(os.getenv("PDF_RENDER_SCALE", "1.35")),
        pdf_page_max_tokens=int(os.getenv("PDF_PAGE_MAX_TOKENS", "1200")),
        pdf_max_pages=int(os.getenv("PDF_MAX_PAGES", "0")),
        summary_model=os.getenv("SUMMARY_MODEL", "gpt-4o-mini").strip(),
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small").strip(),
    )

    for path in [
        settings.data_dir,
        settings.uploads_dir,
        settings.transcripts_dir,
        settings.vector_store_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)

    return settings
