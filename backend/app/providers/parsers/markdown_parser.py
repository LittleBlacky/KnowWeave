from __future__ import annotations

import re

from app.providers.parsers.base import BlockPosition, ParsedBlock, ParserResult, ParserWarning


class MarkdownParser:
    parser_name = "markdown_parser"
    parser_version = "0.1.0"

    def parse(self, content: bytes, *, filename: str) -> ParserResult:
        text = content.decode("utf-8-sig", errors="replace").replace("\r\n", "\n")
        blocks = _markdown_blocks(text)
        warnings = []
        if not text.strip():
            warnings.append(ParserWarning(code="PARSER_OUTPUT_EMPTY", message="No markdown content extracted."))
        if any(block.block_type == "table" for block in blocks):
            warnings.append(
                ParserWarning(
                    code="TABLE_AS_PLACEHOLDER",
                    message="Markdown tables were preserved as placeholder blocks.",
                )
            )
        return ParserResult(
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            raw_text=text,
            blocks=blocks,
            metadata={"filename": filename},
            warnings=warnings,
        )


def _markdown_blocks(text: str) -> list[ParsedBlock]:
    lines = text.split("\n")
    blocks: list[ParsedBlock] = []
    index = 0
    char_offsets = _line_char_offsets(lines)

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue

        if stripped.startswith("```"):
            start = index
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                index += 1
            if index < len(lines):
                index += 1
            blocks.append(_block(blocks, "code", lines, start, index - 1, char_offsets))
            continue

        heading_match = re.match(r"^(#{1,6})\s+", stripped)
        if heading_match:
            block = _block(blocks, "heading", lines, index, index, char_offsets)
            block.metadata["heading_level"] = len(heading_match.group(1))
            blocks.append(block)
            index += 1
            continue

        if _is_table_line(stripped):
            start = index
            index += 1
            while index < len(lines) and _is_table_line(lines[index].strip()):
                index += 1
            block = _block(blocks, "table", lines, start, index - 1, char_offsets)
            block.metadata["is_placeholder"] = True
            blocks.append(block)
            continue

        if re.match(r"^([-*+]|\d+\.)\s+", stripped):
            start = index
            index += 1
            while index < len(lines) and re.match(r"^([-*+]|\d+\.)\s+", lines[index].strip()):
                index += 1
            blocks.append(_block(blocks, "list", lines, start, index - 1, char_offsets))
            continue

        start = index
        index += 1
        while index < len(lines) and lines[index].strip() and not _starts_special_block(lines[index]):
            index += 1
        blocks.append(_block(blocks, "paragraph", lines, start, index - 1, char_offsets))

    return blocks


def _starts_special_block(line: str) -> bool:
    stripped = line.strip()
    return bool(
        stripped.startswith("```")
        or re.match(r"^(#{1,6})\s+", stripped)
        or _is_table_line(stripped)
        or re.match(r"^([-*+]|\d+\.)\s+", stripped)
    )


def _is_table_line(stripped: str) -> bool:
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def _line_char_offsets(lines: list[str]) -> list[int]:
    offsets: list[int] = []
    cursor = 0
    for line in lines:
        offsets.append(cursor)
        cursor += len(line) + 1
    return offsets


def _block(
    blocks: list[ParsedBlock],
    block_type: str,
    lines: list[str],
    start: int,
    end: int,
    offsets: list[int],
) -> ParsedBlock:
    raw_content = "\n".join(lines[start : end + 1])
    return ParsedBlock(
        block_index=len(blocks),
        block_type=block_type,
        raw_content=raw_content,
        normalized_content=raw_content.strip(),
        position=BlockPosition(
            line_start=start + 1,
            line_end=end + 1,
            char_start=offsets[start],
            char_end=offsets[end] + len(lines[end]),
        ),
    )
