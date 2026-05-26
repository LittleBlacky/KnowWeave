from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.files import KnowledgeFile
from app.providers.storage import LocalStorageProvider

SUPPORTED_FILE_TYPES = {
    ".txt": "txt",
    ".md": "md",
    ".markdown": "md",
    ".pdf": "pdf",
    ".docx": "docx",
}


class UnsupportedFileTypeError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="FILE_TYPE_NOT_SUPPORTED",
            message="Only txt, md, pdf and docx files are supported in MVP.",
            status_code=400,
        )


class FileTooLargeError(AppError):
    def __init__(self, max_upload_mb: int) -> None:
        super().__init__(
            code="FILE_TOO_LARGE",
            message=f"Files must be {max_upload_mb} MB or smaller.",
            status_code=400,
            details={"max_upload_mb": max_upload_mb},
        )


class FileEmptyError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="FILE_EMPTY",
            message="Uploaded file is empty.",
            status_code=400,
        )


class FileNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(code="FILE_NOT_FOUND", message="File not found.", status_code=404)


class FileService:
    def __init__(
        self,
        *,
        session: Session,
        storage: LocalStorageProvider,
        max_upload_mb: int = 20,
    ) -> None:
        self.session = session
        self.storage = storage
        self.max_upload_mb = max_upload_mb

    def create_file(
        self,
        *,
        filename: str,
        content_type: str,
        content: bytes,
        directory_path: str = "",
    ) -> KnowledgeFile:
        suffix = Path(filename).suffix.lower()
        file_type = SUPPORTED_FILE_TYPES.get(suffix)
        if file_type is None:
            raise UnsupportedFileTypeError()
        if not content:
            raise FileEmptyError()
        max_bytes = self.max_upload_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise FileTooLargeError(self.max_upload_mb)

        storage_path = self.storage.save(content=content, suffix=suffix)
        record = KnowledgeFile(
            name=filename,
            original_filename=filename,
            file_type=file_type,
            mime_type=content_type or "application/octet-stream",
            size_bytes=len(content),
            sha256=sha256(content).hexdigest(),
            storage_path=storage_path,
            directory_path=directory_path,
            status="uploaded",
            metadata_={},
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def list_files(self) -> list[KnowledgeFile]:
        statement = (
            select(KnowledgeFile)
            .where(KnowledgeFile.deleted_at.is_(None))
            .where(KnowledgeFile.status != "soft_deleted")
            .order_by(KnowledgeFile.created_at.desc())
        )
        return list(self.session.scalars(statement).all())

    def get_file(self, file_id: UUID, *, include_deleted: bool = False) -> KnowledgeFile:
        record = self.session.get(KnowledgeFile, file_id)
        if record is None:
            raise FileNotFoundError()
        if not include_deleted and (record.deleted_at is not None or record.status == "soft_deleted"):
            raise FileNotFoundError()
        return record

    def soft_delete_file(self, file_id: UUID) -> None:
        record = self.get_file(file_id)
        record.status = "soft_deleted"
        record.deleted_at = datetime.now(timezone.utc)
        self.session.add(record)
        self.session.commit()
