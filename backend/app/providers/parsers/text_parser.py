from __future__ import annotations

from app.providers.parsers.base import BlockPosition, ParsedBlock, ParserResult, ParserWarning


class TextParser:
    parser_name = "text_parser"
    parser_version = "0.1.0"

    def parse(self, content: bytes, *, filename: str) -> ParserResult:
        text = content.decode("utf-8-sig", errors="replace").replace("\r\n", "\n")
        blocks = _paragraph_blocks(text)
        warnings = []
        if not text.strip():
            warnings.append(ParserWarning(code="PARSER_OUTPUT_EMPTY", message="No text content extracted."))
        return ParserResult(
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            raw_text=text,
            blocks=blocks,
            metadata={"filename": filename},
            warnings=warnings,
        )


def _paragraph_blocks(text: str) -> list[ParsedBlock]:
    blocks: list[ParsedBlock] = []
    current_lines: list[str] = []
    current_start: int | None = None
    char_cursor = 0
    block_char_start: int | None = None

    for line_number, line in enumerate(text.split("\n"), start=1):
        line_start_char = char_cursor
        stripped = line.strip()
        if stripped:
            if current_start is None:
                current_start = line_number
                block_char_start = line_start_char
            current_lines.append(line)
        elif current_lines and current_start is not None:
            raw_content = "\n".join(current_lines)
            blocks.append(
                ParsedBlock(
                    block_index=len(blocks),
                    block_type="paragraph",
                    raw_content=raw_content,
                    normalized_content=raw_content.strip(),
                    position=BlockPosition(
                        line_start=current_start,
                        line_end=line_number - 1,
                        char_start=block_char_start,
                        char_end=line_start_char - 1,
                    ),
                )
            )
            current_lines = []
            current_start = None
            block_char_start = None
        char_cursor += len(line) + 1

    if current_lines and current_start is not None:
        raw_content = "\n".join(current_lines)
        blocks.append(
            ParsedBlock(
                block_index=len(blocks),
                block_type="paragraph",
                raw_content=raw_content,
                normalized_content=raw_content.strip(),
                position=BlockPosition(
                    line_start=current_start,
                    line_end=len(text.split("\n")),
                    char_start=block_char_start,
                    char_end=len(text),
                ),
            )
        )

    return blocks
