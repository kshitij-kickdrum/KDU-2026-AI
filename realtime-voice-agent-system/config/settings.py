from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class ConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openrouter_api_key: str | None
    openrouter_base_url: str
    llm_model: str
    transcription_model: str
    audio_sample_rate: int
    audio_silence_threshold: float
    audio_speech_min_duration_ms: int
    audio_silence_min_duration_ms: int
    sqlite_db_path: Path
    faiss_index_path: Path
    faiss_metadata_path: Path
    log_file_path: Path
    sqlite_max_connections: int
    faiss_max_connections: int
    queue_timeout_seconds: float

    @classmethod
    def load(cls, require_api_keys: bool = True) -> "Settings":
        load_dotenv()
        _warn_if_env_not_ignored()
        openai_key_name = "OPENAI" + "_API_KEY"
        openrouter_key_name = "OPENROUTER" + "_API_KEY"
        missing = []
        if require_api_keys:
            for name in (openai_key_name, openrouter_key_name):
                if not os.getenv(name):
                    missing.append(name)
        if missing:
            raise ConfigurationError(
                "Missing required environment variable(s): " + ", ".join(missing)
            )

        return cls(
            openai_api_key=os.getenv(openai_key_name),
            openrouter_api_key=os.getenv(openrouter_key_name),
            openrouter_base_url=os.getenv(
                "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
            ),
            llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            transcription_model=os.getenv(
                "TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe"
            ),
            audio_sample_rate=int(os.getenv("AUDIO_SAMPLE_RATE", "16000")),
            audio_silence_threshold=float(
                os.getenv("AUDIO_SILENCE_THRESHOLD", "500")
            ),
            audio_speech_min_duration_ms=int(
                os.getenv("AUDIO_SPEECH_MIN_DURATION_MS", "300")
            ),
            audio_silence_min_duration_ms=int(
                os.getenv("AUDIO_SILENCE_MIN_DURATION_MS", "700")
            ),
            sqlite_db_path=Path(os.getenv("SQLITE_DB_PATH", "data/customer_billing.db")),
            faiss_index_path=Path(os.getenv("FAISS_INDEX_PATH", "data/faiss_index.index")),
            faiss_metadata_path=Path(
                os.getenv("FAISS_METADATA_PATH", "data/faiss_metadata.json")
            ),
            log_file_path=Path(os.getenv("LOG_FILE_PATH", "logs/session.ndjson")),
            sqlite_max_connections=int(os.getenv("SQLITE_MAX_CONNECTIONS", "5")),
            faiss_max_connections=int(os.getenv("FAISS_MAX_CONNECTIONS", "10")),
            queue_timeout_seconds=float(os.getenv("QUEUE_TIMEOUT_SECONDS", "5")),
        )


def _warn_if_env_not_ignored() -> None:
    gitignore = Path(".gitignore")
    if not gitignore.exists():
        print("[settings] Warning: .gitignore missing; .env must not be committed.", file=sys.stderr)
        return
    ignored = {line.strip() for line in gitignore.read_text(encoding="utf-8").splitlines()}
    if ".env" not in ignored:
        print("[settings] Warning: .env is not listed in .gitignore.", file=sys.stderr)
