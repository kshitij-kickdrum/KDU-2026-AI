from __future__ import annotations

from io import BytesIO

import pytest

from src.utils.validators import sanitize_filename, validate_file_size, validate_file_type


class DummyUpload:
    def __init__(self, name: str, mime: str, content: bytes) -> None:
        self.name = name
        self.type = mime
        self.size = len(content)
        self._content = content

    def getvalue(self) -> bytes:
        return self._content


def test_validate_file_type_accepts_supported() -> None:
    assert validate_file_type("sample.pdf", "application/pdf") == "pdf"
    assert validate_file_type("a.jpg", "image/jpeg") == "image"
    assert validate_file_type("a.mp3", "audio/mpeg") == "audio"


def test_validate_file_type_rejects_unsupported() -> None:
    with pytest.raises(ValueError):
        validate_file_type("a.exe", "application/octet-stream")


def test_validate_file_size() -> None:
    validate_file_size(1024, 1)
    with pytest.raises(ValueError):
        validate_file_size(2 * 1024 * 1024, 1)


def test_sanitize_filename() -> None:
    assert sanitize_filename("my file@#.pdf") == "my_file__.pdf"
