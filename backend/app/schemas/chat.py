from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatSessionCreate(BaseModel):
    title: str = "New chat"


class ChatSessionRead(BaseModel):
    id: UUID
    title: str
    scope: dict[str, object]
    created_at: datetime
    updated_at: datetime


class ChatSessionList(BaseModel):
    items: list[ChatSessionRead]
    total: int


class ChatMessageRead(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content_markdown: str
    status: str
    model_provider: str | None = None
    model_name: str | None = None
    prompt_version: str | None = None
    created_at: datetime


class ChatSessionDetail(ChatSessionRead):
    messages: list[ChatMessageRead]


class ChatMessageRequest(BaseModel):
    question: str
    top_k: int = Field(default=5, ge=1, le=20)


class CitationRead(BaseModel):
    id: UUID
    target_type: str
    target_id: UUID
    file_id: UUID | None = None
    chunk_id: UUID | None = None
    source_span_id: UUID | None = None
    label: str | None = None
    preview_text: str
    source_available: bool


class CitationList(BaseModel):
    items: list[CitationRead]
    total: int
