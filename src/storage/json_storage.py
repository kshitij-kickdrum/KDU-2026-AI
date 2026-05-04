from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonStorage:
    def __init__(self, transcripts_dir: Path) -> None:
        self.transcripts_dir = transcripts_dir
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)

    def save_transcript(self, file_id: str, payload: dict[str, Any]) -> str:
        path = self.transcripts_dir / f"{file_id}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=True, indent=2)
        return str(path)

    def load_transcript(self, file_id: str) -> dict[str, Any]:
        path = self.transcripts_dir / f"{file_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Transcript not found for file_id={file_id}")
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
