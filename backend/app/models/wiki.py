from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class WikiPage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "wiki_pages"

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    wiki_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), default="draft", nullable=False, index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    source_file_id: Mapped[UUID | None] = mapped_column(ForeignKey("knowledge_files.id"))
    generation_prompt_version: Mapped[str | None] = mapped_column(String(64))
    search_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column()

    revisions: Mapped[list["WikiRevision"]] = relationship(
        back_populates="wiki_page",
        order_by="WikiRevision.revision_number.desc()",
        cascade="all, delete-orphan",
    )


class WikiRevision(UUIDPrimaryKeyMixin, Base):
    """Immutable snapshot of a Wiki page at a point in time."""

    __tablename__ = "wiki_revisions"

    wiki_page_id: Mapped[UUID] = mapped_column(ForeignKey("wiki_pages.id"), nullable=False, index=True)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    change_summary: Mapped[str] = mapped_column(String(1024), default="", nullable=False)
    edit_source: Mapped[str] = mapped_column(String(64), default="manual", nullable=False)
    # "manual" | "ai_generated" | "ai_regenerated" | "rollback"
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    wiki_page: Mapped[WikiPage] = relationship(back_populates="revisions")
