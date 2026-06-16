from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EvaluationSampleCreate(BaseModel):
    question: str
    expected_answer: str | None = None
    expected_source_files: list[UUID] = Field(default_factory=list)
    expected_source_chunks: list[UUID] = Field(default_factory=list)
    created_from: str = "manual"
    status: str = "candidate"
    difficulty: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class EvaluationSampleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question: str
    expected_answer: str | None = None
    expected_source_files: list[UUID]
    expected_source_chunks: list[UUID]
    created_from: str
    source_chat_message_id: UUID | None = None
    source_feedback_id: UUID | None = None
    status: str
    difficulty: str | None = None
    metadata_: dict[str, object]
    created_at: datetime
    updated_at: datetime


class EvaluationSampleList(BaseModel):
    items: list[EvaluationSampleRead]
    total: int


class EvaluationSampleUpdate(BaseModel):
    question: str | None = None
    expected_answer: str | None = None
    status: str | None = None
    difficulty: str | None = None
