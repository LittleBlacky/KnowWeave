from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Feedback(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "feedback"

    target_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    feedback_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    comment: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), default="open", nullable=False, index=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)


class EvaluationSample(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evaluation_samples"

    question: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[str | None] = mapped_column(Text)
    expected_source_files: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    expected_source_chunks: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_from: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_chat_message_id: Mapped[UUID | None] = mapped_column()
    source_feedback_id: Mapped[UUID | None] = mapped_column()
    status: Mapped[str] = mapped_column(String(64), default="candidate", nullable=False, index=True)
    difficulty: Mapped[str | None] = mapped_column(String(64))
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)
