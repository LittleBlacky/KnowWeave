from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class LLMResult:
    content: str
    model_name: str
    usage: dict[str, int]
    raw_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMStreamEvent:
    type: str
    text: str
    finish_reason: str | None = None
    usage: dict[str, int] | None = None


class LLMProvider(Protocol):
    async def generate(
        self,
        *,
        messages: list[dict[str, str]],
        options: dict[str, Any],
    ) -> LLMResult:
        raise NotImplementedError

    def stream(
        self,
        *,
        messages: list[dict[str, str]],
        options: dict[str, Any],
    ) -> AsyncIterator[LLMStreamEvent]:
        raise NotImplementedError

    async def health_check(self) -> dict[str, Any]:
        raise NotImplementedError


class LLMProviderError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
