from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.tags import TagRead


class KnowledgeUnitWriteRequest(BaseModel):
    title: str
    content: str
    unit_type: str = "concept"
    summary: str | None = None
    status: str = "draft"
    applicable_scope: str | None = None
    tag_ids: list[UUID] = Field(default_factory=list)
    source_chunk_ids: list[UUID] = Field(default_factory=list)


class KnowledgeUnitSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    knowledge_unit_id: UUID
    file_id: UUID | None = None
    chunk_id: UUID | None = None
    source_span_id: UUID | None = None
    source_type: str
    source_label: str
    source_available: bool
    created_at: datetime


class KnowledgeUnitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    unit_type: str
    content: str
    summary: str | None = None
    status: str
    trust_level: int | None = None
    applicable_scope: str | None = None
    created_from: str
    search_text: str
    metadata_: dict[str, object]
    source_count: int = 0
    tags: list[TagRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    verified_at: datetime | None = None
    archived_at: datetime | None = None


class KnowledgeUnitDetail(KnowledgeUnitRead):
    sources: list[KnowledgeUnitSourceRead] = Field(default_factory=list)


class KnowledgeUnitList(BaseModel):
    items: list[KnowledgeUnitRead]
    total: int


class KnowledgeUnitMergeRequest(BaseModel):
    source_ids: list[UUID]
    title: str


class KnowledgeUnitSplitRequest(BaseModel):
    source_id: UUID
    titles: list[str]
    content_splits: list[str]


class KnowledgeUnitList(BaseModel):
    items: list[KnowledgeUnitRead]
    total: int
