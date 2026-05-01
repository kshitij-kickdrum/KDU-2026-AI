from __future__ import annotations

import logging
from pathlib import Path

from src.utils.config import AppConfig


def configure_logging(config: AppConfig) -> None:
    config.log_file.parent.mkdir(parents=True, exist_ok=True)
    level = getattr(logging, config.log_level.upper(), logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    file_handler = logging.FileHandler(Path(config.log_file), encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)
