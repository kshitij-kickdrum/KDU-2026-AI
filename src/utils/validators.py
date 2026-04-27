from __future__ import annotations

import re
from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf": "pdf", ".jpg": "image", ".jpeg": "image", ".png": "image", ".mp3": "audio", ".wav": "audio"}
SUPPORTED_MIME_PREFIXES = {
    "application/pdf": "pdf",
    "image/": "image",
    "audio/": "audio",
}


def validate_file_type(filename: str, mime_type: str | None = None) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {extension}")

    detected_type = SUPPORTED_EXTENSIONS[extension]
    if mime_type:
        mime = mime_type.lower()
        if not any(mime == k or mime.startswith(k) for k in SUPPORTED_MIME_PREFIXES):
            raise ValueError(f"Unsupported MIME type: {mime_type}")
    return detected_type


def validate_file_size(size_bytes: int, max_size_mb: int) -> None:
    if size_bytes <= 0:
        raise ValueError("File is empty")
    max_bytes = max_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise ValueError(f"File exceeds maximum size of {max_size_mb}MB")


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", filename).strip("._")
    if not cleaned:
        cleaned = "uploaded_file"

    stem = Path(cleaned).stem[: max_length - 10]
    suffix = Path(cleaned).suffix[:10]
    return f"{stem}{suffix}"[:max_length]
