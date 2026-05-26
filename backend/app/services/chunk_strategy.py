from __future__ import annotations

from dataclasses import dataclass
import re
from uuid import UUID


@dataclass(frozen=True)
class ChunkStrategyOptions:
    strategy: str = "hybrid"
    max_chars: int = 1200
    min_chars: int = 80
    overlap_chars: int = 120
    include_headings: bool = True


@dataclass(frozen=True)
class BlockForChunking:
    block_id: UUID
    block_type: str
    raw_content: str
    line_start: int | None = None
    line_end: int | None = None
    page_number: int | None = None
    char_start: int | None = None
    char_end: int | None = None


@dataclass(frozen=True)
class SourceLocator:
    block_id: UUID
    line_start: int | None = None
    line_end: int | None = None
    page_number: int | None = None
    char_start: int | None = None
    char_end: int | None = None
    preview_text: str = ""


@dataclass(frozen=True)
class ChunkCandidate:
    chunk_type: str
    raw_content: str
    source: SourceLocator
    quality_signals: list[dict[str, str]]


def build_chunk_candidates(
    blocks: list[BlockForChunking],
    *,
    options: ChunkStrategyOptions | None = None,
) -> list[ChunkCandidate]:
    effective_options = options or ChunkStrategyOptions()
    split_candidates: list[ChunkCandidate] = []

    for block in blocks:
        content = block.raw_content.strip()
        if not content:
            continue
        for text in _split_block_text(content, effective_options.max_chars):
            split_candidates.append(_candidate_from_block(block, text))

    return _merge_short_candidates(split_candidates, effective_options.min_chars)


def _split_block_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    sentences = [part.strip() for part in re.findall(r"[^。；.\n]+[。；.]?|[^\n]+", text) if part.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = sentence
    if current:
        chunks.append(current)
    return chunks or [text[:max_chars]]


def _candidate_from_block(block: BlockForChunking, text: str) -> ChunkCandidate:
    chunk_type = "table" if block.block_type == "table" else "text"
    return ChunkCandidate(
        chunk_type=chunk_type,
        raw_content=text,
        source=SourceLocator(
            block_id=block.block_id,
            line_start=block.line_start,
            line_end=block.line_end,
            page_number=block.page_number,
            char_start=block.char_start,
            char_end=block.char_end,
            preview_text=text,
        ),
        quality_signals=[],
    )


def _merge_short_candidates(candidates: list[ChunkCandidate], min_chars: int) -> list[ChunkCandidate]:
    merged: list[ChunkCandidate] = []
    pending: ChunkCandidate | None = None

    for candidate in candidates:
        if pending is None:
            pending = candidate
            continue
        if len(pending.raw_content) < min_chars and pending.chunk_type == "text" and candidate.chunk_type == "text":
            pending = _merge_pair(pending, candidate)
            continue
        merged.append(pending)
        pending = candidate

    if pending is not None:
        merged.append(pending)
    return merged


def _merge_pair(first: ChunkCandidate, second: ChunkCandidate) -> ChunkCandidate:
    content = f"{first.raw_content}\n\n{second.raw_content}"
    return ChunkCandidate(
        chunk_type="text",
        raw_content=content,
        source=SourceLocator(
            block_id=first.source.block_id,
            line_start=_minimum(first.source.line_start, second.source.line_start),
            line_end=_maximum(first.source.line_end, second.source.line_end),
            page_number=first.source.page_number or second.source.page_number,
            char_start=_minimum(first.source.char_start, second.source.char_start),
            char_end=_maximum(first.source.char_end, second.source.char_end),
            preview_text=content,
        ),
        quality_signals=first.quality_signals + second.quality_signals,
    )


def _minimum(first: int | None, second: int | None) -> int | None:
    values = [value for value in (first, second) if value is not None]
    return min(values) if values else None


def _maximum(first: int | None, second: int | None) -> int | None:
    values = [value for value in (first, second) if value is not None]
    return max(values) if values else None
