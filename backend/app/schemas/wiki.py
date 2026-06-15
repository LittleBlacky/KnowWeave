from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WikiTopicRequest(BaseModel):
    theme: str
    file_ids: list[UUID] | None = None
    knowledge_unit_ids: list[UUID] | None = None


class WikiPageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    wiki_type: str
    status: str
    summary: str | None = None
    content_markdown: str
    source_file_id: UUID | None = None
    generation_prompt_version: str | None = None
    search_text: str
    metadata_: dict[str, object]
    created_at: datetime
    updated_at: datetime
    verified_at: datetime | None = None


class WikiPageList(BaseModel):
    items: list[WikiPageRead]
    total: int


class WikiUpdateRequest(BaseModel):
    title: str | None = None
    content_markdown: str | None = None
    change_summary: str
    status: str | None = None
    summary: str | None = None


class WikiRevisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    wiki_page_id: UUID
    revision_number: int
    title: str
    content_markdown: str
    summary: str | None = None
    status: str
    change_summary: str
    edit_source: str
    created_at: datetime
