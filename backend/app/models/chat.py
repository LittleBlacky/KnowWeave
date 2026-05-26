from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ChatSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_sessions"

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    scope: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class ChatMessage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "chat_messages"

    session_id: Mapped[UUID] = mapped_column(ForeignKey("chat_sessions.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    model_provider: Mapped[str | None] = mapped_column(String(128))
    model_name: Mapped[str | None] = mapped_column(String(128))
    prompt_version: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    session: Mapped[ChatSession] = relationship(back_populates="messages")
    retrieved_contexts: Mapped[list[RetrievedContext]] = relationship(back_populates="chat_message")


class RetrievedContext(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "retrieved_contexts"

    retrieval_run_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    chat_message_id: Mapped[UUID | None] = mapped_column(ForeignKey("chat_messages.id"))
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    result_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    result_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    retrieval_strategy: Mapped[str] = mapped_column(String(64), nullable=False)
    retrieval_params: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    used_in_answer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    chat_message: Mapped[ChatMessage | None] = relationship(back_populates="retrieved_contexts")


class Citation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "citations"

    target_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    file_id: Mapped[UUID | None] = mapped_column(ForeignKey("knowledge_files.id"))
    chunk_id: Mapped[UUID | None] = mapped_column(ForeignKey("chunks.id"))
    knowledge_unit_id: Mapped[UUID | None] = mapped_column()
    source_span_id: Mapped[UUID | None] = mapped_column(ForeignKey("source_spans.id"))
    label: Mapped[str | None] = mapped_column(String(255))
    preview_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
