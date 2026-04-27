from __future__ import annotations

from src.core.file_manager import FileManager


class DummyUpload:
    def __init__(self, name: str, mime: str, content: bytes) -> None:
        self.name = name
        self.type = mime
        self.size = len(content)
        self._content = content

    def getvalue(self) -> bytes:
        return self._content


def test_file_upload(temp_db, tmp_path) -> None:
    manager = FileManager(temp_db, tmp_path / "uploads", max_file_size_mb=1)
    upload = DummyUpload("doc.pdf", "application/pdf", b"%PDF-1.4 sample")

    response = manager.upload_file(upload)
    assert response.status == "pending"

    status = manager.get_file_status(response.file_id)
    assert status.processing_status == "pending"
