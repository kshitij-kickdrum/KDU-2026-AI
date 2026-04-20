from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from urllib.parse import urlparse
from typing import Literal

try:
    import magic  # type: ignore[import-untyped]
except Exception:  # noqa: BLE001
    magic = None  # type: ignore[assignment]


def is_allowed_url(url: str, allowed_domains: list[str]) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = (parsed.hostname or "").lower().strip(".")
    if not host:
        return False
    if host in {"localhost"}:
        return False
    try:
        ipaddress.ip_address(host)
        return False
    except ValueError:
        pass
    return any(host == domain or host.endswith(f".{domain}") for domain in allowed_domains)


def sanitize_html_text(text: str) -> str:
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?is)on\w+\s*=\s*['\"].*?['\"]", "", text)
    return text


def validate_pdf_path(path: str, max_size_mb: int) -> bool:
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return False
    if file_path.suffix.lower() != ".pdf":
        return False
    if file_path.stat().st_size > max_size_mb * 1024 * 1024:
        return False
    return detect_file_type(str(file_path)) == "pdf"


def detect_file_type(path: str) -> Literal["pdf", "unknown"]:
    file_path = Path(path)
    try:
        with file_path.open("rb") as fh:
            head = fh.read(8)
        if head.startswith(b"%PDF-"):
            return "pdf"
    except Exception:  # noqa: BLE001
        return "unknown"

    if magic:
        try:
            mime = magic.from_file(str(file_path), mime=True)
            if mime == "application/pdf":
                return "pdf"
        except Exception:  # noqa: BLE001
            pass
    return "unknown"
