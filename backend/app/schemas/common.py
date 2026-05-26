from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ApiResponse(BaseModel, Generic[DataT]):
    data: DataT | None = None
    error: ErrorPayload | None = None
    request_id: str


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
