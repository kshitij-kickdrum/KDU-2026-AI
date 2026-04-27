from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from src.models.file_models import FileRecord


def test_database_file_crud(temp_db) -> None:
    record = FileRecord(
        file_id=str(uuid4()),
        display_id="PDF1",
        filename="sample.pdf",
        file_type="pdf",
        file_path="data/uploads/a.pdf",
        file_size_bytes=123,
        upload_timestamp=datetime.now(timezone.utc).isoformat(),
    )
    temp_db.insert_file(record)

    row = temp_db.get_file(record.file_id)
    assert row is not None
    assert row["filename"] == "sample.pdf"

    temp_db.update_file_status(record.file_id, "processing")
    row = temp_db.get_file(record.file_id)
    assert row is not None
    assert row["processing_status"] == "processing"
