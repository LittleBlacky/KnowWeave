from __future__ import annotations

from datetime import datetime
from typing import Any
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


class ParseResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_id: UUID
    parser_name: str
    parser_version: str
    status: str
    raw_text: str
    warnings: list[dict[str, Any]]
    error_message: str | None = None
    parse_metadata: dict[str, Any]
    block_count: int
    created_at: datetime


class DocumentBlockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_id: UUID
    parse_result_id: UUID
    block_index: int
    block_type: str
    raw_content: str
    normalized_content: str | None = None
    is_ignored: bool
    page_number: int | None = None
    line_start: int | None = None
    line_end: int | None = None
    char_start: int | None = None
    char_end: int | None = None
    metadata: dict[str, Any]
    created_at: datetime


class DocumentBlockList(BaseModel):
    items: list[DocumentBlockRead]
    total: int


class SourceSpanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_block_id: UUID | None = None
    page_number: int | None = None
    char_start: int | None = None
    char_end: int | None = None
    line_start: int | None = None
    line_end: int | None = None
    preview_text: str


class ChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_id: UUID
    parse_result_id: UUID
    document_block_id: UUID | None = None
    chunk_index: int
    chunk_type: str
    raw_content: str
    edited_content: str | None = None
    is_manually_edited: bool
    status: str
    summary: str | None = None
    quality_signals: list[dict[str, Any]]
    char_count: int
    search_text: str
    is_searchable: bool
    source_spans: list[SourceSpanRead]


class ChunkList(BaseModel):
    items: list[ChunkRead]
    total: int


class ChunkUpdateRequest(BaseModel):
    edited_content: str | None = None
    status: str | None = None
    summary: str | None = None
