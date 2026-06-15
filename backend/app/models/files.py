from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeFile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_files"

    name: Mapped[str] = mapped_column(String(512), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    directory_path: Mapped[str] = mapped_column(String(1024), default="", nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="uploaded", nullable=False, index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    source_note: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column()

    parse_results: Mapped[list[ParseResult]] = relationship(
        back_populates="file",
        cascade="all, delete-orphan",
    )


class ParseResult(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "parse_results"

    file_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_files.id"), nullable=False)
    parser_name: Mapped[str] = mapped_column(String(128), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    raw_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    warnings: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    parse_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    file: Mapped[KnowledgeFile] = relationship(back_populates="parse_results")
    document_blocks: Mapped[list[DocumentBlock]] = relationship(
        back_populates="parse_result",
        cascade="all, delete-orphan",
    )


class DocumentBlock(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "document_blocks"

    file_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_files.id"), nullable=False)
    parse_result_id: Mapped[UUID] = mapped_column(ForeignKey("parse_results.id"), nullable=False)
    parent_block_id: Mapped[UUID | None] = mapped_column(ForeignKey("document_blocks.id"))
    block_index: Mapped[int] = mapped_column(Integer, nullable=False)
    block_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_content: Mapped[str | None] = mapped_column(Text)
    is_ignored: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer)
    char_start: Mapped[int | None] = mapped_column(Integer)
    char_end: Mapped[int | None] = mapped_column(Integer)
    bbox: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    asset_ref: Mapped[str | None] = mapped_column(Text)
    context_before: Mapped[str | None] = mapped_column(Text)
    context_after: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    parse_result: Mapped[ParseResult] = relationship(back_populates="document_blocks")


class Chunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chunks"

    file_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_files.id"), nullable=False)
    parse_result_id: Mapped[UUID] = mapped_column(ForeignKey("parse_results.id"), nullable=False)
    document_block_id: Mapped[UUID | None] = mapped_column(ForeignKey("document_blocks.id"))
    parent_chunk_id: Mapped[UUID | None] = mapped_column(ForeignKey("chunks.id"))
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    edited_content: Mapped[str | None] = mapped_column(Text)
    is_manually_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), default="draft", nullable=False, index=True)
    quality_signals: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    search_text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)
    is_searchable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)


class SourceSpan(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "source_spans"

    file_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_files.id"), nullable=False)
    chunk_id: Mapped[UUID | None] = mapped_column(ForeignKey("chunks.id"))
    document_block_id: Mapped[UUID | None] = mapped_column(ForeignKey("document_blocks.id"))
    page_number: Mapped[int | None] = mapped_column(Integer)
    char_start: Mapped[int | None] = mapped_column(Integer)
    char_end: Mapped[int | None] = mapped_column(Integer)
    line_start: Mapped[int | None] = mapped_column(Integer)
    line_end: Mapped[int | None] = mapped_column(Integer)
    column_start: Mapped[int | None] = mapped_column(Integer)
    column_end: Mapped[int | None] = mapped_column(Integer)
    bbox: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    selector: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    preview_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
