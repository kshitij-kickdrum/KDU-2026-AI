from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src.models.file_models import FileRecord, FileStatusResponse, FileUploadResponse
from src.storage.database import Database
from src.utils.validators import sanitize_filename, validate_file_size, validate_file_type


class FileManager:
    def __init__(self, db: Database, uploads_dir: Path, max_file_size_mb: int) -> None:
        self.db = db
        self.uploads_dir = uploads_dir
        self.max_file_size_mb = max_file_size_mb
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    def upload_file(self, file: object) -> FileUploadResponse:
        filename = sanitize_filename(getattr(file, "name"))
        mime_type = getattr(file, "type", None)

        if hasattr(file, "size") and file.size is not None:
            size_bytes = int(file.size)
            content = file.getvalue()
        else:
            content = file.getvalue()
            size_bytes = len(content)

        file_type = validate_file_type(filename, mime_type)
        validate_file_size(size_bytes, self.max_file_size_mb)

        file_id = str(uuid4())
        display_id = self.db.allocate_display_id(file_type)
        stored_name = f"{file_id}_{filename}"
        target_path = self.uploads_dir / stored_name
        target_path.write_bytes(content)

        now = datetime.now(timezone.utc).isoformat()
        record = FileRecord(
            file_id=file_id,
            display_id=display_id,
            filename=filename,
            file_type=file_type,
            file_path=str(target_path),
            file_size_bytes=size_bytes,
            upload_timestamp=now,
            processing_status="pending",
            created_at=now,
            updated_at=now,
        )
        self.db.insert_file(record)

        return FileUploadResponse(
            file_id=file_id,
            display_id=display_id,
            filename=filename,
            file_type=file_type,
            status="pending",
            message="File uploaded successfully",
        )

    def get_file_status(self, file_id: str) -> FileStatusResponse:
        row = self.db.get_file(file_id)
        if row is None:
            raise ValueError(f"File not found: {file_id}")

        status = row["processing_status"]
        progress = 0
        if status == "processing":
            progress = 50
        elif status == "completed":
            progress = 100

        return FileStatusResponse(
            file_id=file_id,
            filename=row["filename"],
            processing_status=status,
            progress_percentage=progress,
            error_message=row.get("error_message"),
        )

    def delete_file(self, file_id: str) -> None:
        row = self.db.get_file(file_id)
        if row is None:
            raise ValueError(f"File not found: {file_id}")

        upload_path = Path(row["file_path"])
        transcript_path = Path(row["transcript_path"]) if row.get("transcript_path") else None

        self.db.delete_file(file_id)

        if upload_path.exists():
            upload_path.unlink()
        if transcript_path and transcript_path.exists():
            transcript_path.unlink()
