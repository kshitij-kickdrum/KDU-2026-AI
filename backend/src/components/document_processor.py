from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
try:
    import pdfplumber
except Exception:  # noqa: BLE001
    pdfplumber = None  # type: ignore[assignment]

from src.models import ProcessedDocument
from src.utils.malware_scan import MalwareScanner
from src.utils.security_events import log_security_event
from src.utils.security import is_allowed_url, sanitize_html_text, validate_pdf_path
from src.utils.resilience import retry
from src.utils.text import normalize_whitespace

logger = logging.getLogger(__name__)


class DocumentProcessor:
    def __init__(
        self,
        allowed_domains: list[str],
        max_file_size_mb: int = 50,
        timeout_seconds: int = 30,
        malware_scanner: MalwareScanner | None = None,
    ) -> None:
        self.allowed_domains = allowed_domains
        self.max_file_size_mb = max_file_size_mb
        self.timeout_seconds = timeout_seconds
        self.malware_scanner = malware_scanner

    def process_url(self, url: str) -> ProcessedDocument:
        if not is_allowed_url(url, self.allowed_domains):
            log_security_event(
                event_type="url_rejected",
                severity="medium",
                details={"url": url, "reason": "domain_not_allowed"},
            )
            raise ValueError("URL domain is not allowed")
        if self.malware_scanner:
            scan = self.malware_scanner.scan_url(url)
            if scan.is_malicious:
                log_security_event(
                    event_type="url_malware_blocked",
                    severity="high",
                    details={"url": url, "reason": scan.reason},
                )
                raise ValueError(f"URL blocked by malware scan: {scan.reason}")
        response = retry(lambda: requests.get(url, timeout=self.timeout_seconds), attempts=3)
        response.raise_for_status()
        raw_html = response.text
        cleaned_html = sanitize_html_text(raw_html)
        soup = BeautifulSoup(cleaned_html, "html.parser")
        for tag in soup(["header", "footer", "nav", "aside", "script", "style"]):
            tag.decompose()
        title = normalize_whitespace((soup.title.string if soup.title else "Untitled") or "Untitled")
        body = normalize_whitespace(soup.get_text(" ", strip=True))
        if not body:
            raise ValueError("No text extracted from URL")
        return ProcessedDocument(
            title=title or "Untitled",
            content=body,
            source=url,
            source_type="url",
            metadata={
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "status_code": response.status_code,
            },
        )

    def process_pdf(self, file_path: str) -> ProcessedDocument:
        return self.process_pdf_with_metadata(file_path=file_path)

    def process_pdf_with_metadata(
        self,
        file_path: str,
        display_title: str | None = None,
        display_source: str | None = None,
    ) -> ProcessedDocument:
        if not validate_pdf_path(file_path, self.max_file_size_mb):
            log_security_event(
                event_type="pdf_rejected",
                severity="medium",
                details={"file_path": file_path, "reason": "invalid_type_or_size"},
            )
            raise ValueError("Invalid PDF path, type, or size")

        title = display_title or Path(file_path).stem
        text_parts: list[str] = []
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
        except Exception as exc:  # noqa: BLE001
            logger.warning("PyPDF2 extraction failed: %s", exc)
            log_security_event(
                event_type="pdf_extraction_fallback",
                severity="low",
                details={"file_path": file_path, "reason": str(exc)},
            )
            if not pdfplumber:
                raise ValueError(f"Failed to parse PDF: {exc}") from exc
            try:
                with pdfplumber.open(file_path) as pdf:
                    text_parts = [(page.extract_text() or "") for page in pdf.pages]
            except Exception as inner_exc:  # noqa: BLE001
                logger.exception("pdfplumber fallback failed")
                log_security_event(
                    event_type="pdf_extraction_failed",
                    severity="high",
                    details={"file_path": file_path, "reason": str(inner_exc)},
                )
                raise ValueError(f"Failed to parse PDF with fallback: {inner_exc}") from inner_exc

        content = normalize_whitespace("\n".join(text_parts))
        if not content:
            raise ValueError("No text extracted from PDF")

        return ProcessedDocument(
            title=title,
            content=content,
            source=display_source or file_path,
            source_type="pdf",
            metadata={"page_count": len(text_parts)},
        )
