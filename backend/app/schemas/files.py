from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    original_filename: str
    file_type: str
    mime_type: str
    size_bytes: int
    sha256: str
    directory_path: str
    status: str


class FileDetail(FileRead):
    summary: str | None = None
    source_note: str | None = None
    created_at: datetime
    updated_at: datetime


class FileList(BaseModel):
    items: list[FileRead]
    total: int
