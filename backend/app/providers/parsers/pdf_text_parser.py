from __future__ import annotations

import re

from app.providers.parsers.base import BlockPosition, ParsedBlock, ParserResult, ParserWarning


class PdfTextParser:
    parser_name = "pdf_text_parser"
    parser_version = "0.1.0"

    def parse(self, content: bytes, *, filename: str) -> ParserResult:
        raw = content.decode("latin-1", errors="ignore")
        texts = [_decode_pdf_literal(match) for match in re.findall(r"\((.*?)\)\s*Tj", raw, flags=re.S)]
        text = "\n".join(part for part in texts if part.strip()).strip()
        blocks = []
        if text:
            blocks.append(
                ParsedBlock(
                    block_index=0,
                    block_type="paragraph",
                    raw_content=text,
                    normalized_content=text,
                    position=BlockPosition(page_number=1, char_start=0, char_end=len(text)),
                )
            )
        warnings = []
        if not text:
            warnings.append(ParserWarning(code="PARSER_OUTPUT_EMPTY", message="No PDF text content extracted."))
        return ParserResult(
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            raw_text=text,
            blocks=blocks,
            metadata={"filename": filename, "page_count": max(raw.count("/Type /Page"), 1)},
            warnings=warnings,
        )


def _decode_pdf_literal(value: str) -> str:
    return (
        value.replace(r"\(", "(")
        .replace(r"\)", ")")
        .replace(r"\\", "\\")
        .replace(r"\n", "\n")
        .replace(r"\r", "\r")
        .replace(r"\t", "\t")
    )
