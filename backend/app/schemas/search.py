from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str
    target_types: list[str] = Field(default_factory=lambda: ["chunk"])
    filters: dict[str, Any] = Field(default_factory=dict)
    top_k: int = Field(default=10, ge=1, le=50)


class SearchResultRead(BaseModel):
    result_id: UUID
    result_type: str
    title: str
    preview_text: str
    score: Decimal
    rank: int
    source: dict[str, Any]
    status: dict[str, Any]
    metadata: dict[str, Any]


class SearchResponseRead(BaseModel):
    retrieval_run_id: UUID
    query: str
    strategy: str
    results: list[SearchResultRead]
