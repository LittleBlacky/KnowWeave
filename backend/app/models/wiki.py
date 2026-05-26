from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

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
