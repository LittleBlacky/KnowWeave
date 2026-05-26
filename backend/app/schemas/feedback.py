from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    target_type: str
    target_id: UUID
    feedback_type: str
    comment: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class FeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    target_type: str
    target_id: UUID
    feedback_type: str
    comment: str | None = None
    status: str
    metadata_: dict[str, object]
    created_at: datetime
    updated_at: datetime


class FeedbackList(BaseModel):
    items: list[FeedbackRead]
    total: int
