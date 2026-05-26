from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TagWriteRequest(BaseModel):
    name: str
    description: str | None = None
    color: str | None = None


class TagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    color: str | None = None
    binding_count: int = 0
    created_at: datetime
    updated_at: datetime


class TagList(BaseModel):
    items: list[TagRead]
    total: int


class TagBindingRequest(BaseModel):
    tag_id: UUID
    target_type: str
    target_id: UUID


class TagBindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tag_id: UUID
    target_type: str
    target_id: UUID
    created_at: datetime
