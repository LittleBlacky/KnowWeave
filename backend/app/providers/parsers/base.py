from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ParserWarning:
    code: str
    message: str


@dataclass(frozen=True)
class BlockPosition:
    page_number: int | None = None
    line_start: int | None = None
    line_end: int | None = None
    char_start: int | None = None
    char_end: int | None = None


@dataclass(frozen=True)
class ParsedBlock:
    block_index: int
    block_type: str
    raw_content: str
    normalized_content: str | None = None
    position: BlockPosition = field(default_factory=BlockPosition)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParserResult:
    parser_name: str
    parser_version: str
    raw_text: str
    blocks: list[ParsedBlock]
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[ParserWarning] = field(default_factory=list)


class DocumentParser(Protocol):
    parser_name: str
    parser_version: str

    def parse(self, content: bytes, *, filename: str) -> ParserResult:
        raise NotImplementedError
