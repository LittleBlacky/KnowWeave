from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeUnit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_units"

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    unit_type: Mapped[str] = mapped_column(String(64), default="concept", nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), default="draft", nullable=False, index=True)
    trust_level: Mapped[int | None] = mapped_column(Integer)
    applicable_scope: Mapped[str | None] = mapped_column(Text)
    created_from: Mapped[str] = mapped_column(String(64), default="manual", nullable=False, index=True)
    search_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column()
    archived_at: Mapped[datetime | None] = mapped_column()


class KnowledgeUnitSource(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "knowledge_unit_sources"

    knowledge_unit_id: Mapped[UUID] = mapped_column(
        ForeignKey("knowledge_units.id"),
        nullable=False,
        index=True,
    )
    file_id: Mapped[UUID | None] = mapped_column(ForeignKey("knowledge_files.id"), index=True)
    chunk_id: Mapped[UUID | None] = mapped_column(ForeignKey("chunks.id"), index=True)
    source_span_id: Mapped[UUID | None] = mapped_column(ForeignKey("source_spans.id"))
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_label: Mapped[str] = mapped_column(String(255), nullable=False)
    source_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)


class WikiPageUnit(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "wiki_page_units"

    wiki_page_id: Mapped[UUID] = mapped_column(ForeignKey("wiki_pages.id"), nullable=False, index=True)
    knowledge_unit_id: Mapped[UUID] = mapped_column(
        ForeignKey("knowledge_units.id"),
        nullable=False,
        index=True,
    )
    section_anchor: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)


class Tag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str | None] = mapped_column(String(64))


class TagBinding(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "tag_bindings"
    __table_args__ = (
        UniqueConstraint("tag_id", "target_type", "target_id", name="uq_tag_bindings_target"),
    )

    tag_id: Mapped[UUID] = mapped_column(ForeignKey("tags.id"), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
