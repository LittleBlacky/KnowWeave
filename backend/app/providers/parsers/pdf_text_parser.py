from __future__ import annotations

import io

try:
    import pdfplumber  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    pdfplumber = None  # type: ignore[assignment]

from app.providers.parsers.base import BlockPosition, ParsedBlock, ParserResult, ParserWarning


class PdfTextParser:
    parser_name = "pdf_text_parser"
    parser_version = "0.2.0"

    def parse(self, content: bytes, *, filename: str) -> ParserResult:
        warnings: list[ParserWarning] = []
        blocks: list[ParsedBlock] = []
        raw_text_parts: list[str] = []
        page_count = 0

        if pdfplumber is None:
            warnings.append(
                ParserWarning(code="PDFPLUMBER_NOT_INSTALLED", message="pdfplumber is not available.")
            )
            return ParserResult(
                parser_name=self.parser_name,
                parser_version=self.parser_version,
                raw_text="",
                blocks=blocks,
                metadata={"filename": filename},
                warnings=warnings,
            )

        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                page_count = len(pdf.pages)
                block_index = 0
                for page in pdf.pages:
                    text = (page.extract_text() or "").strip()
                    if not text:
                        continue
                    raw_text_parts.append(text)
                    blocks.append(
                        ParsedBlock(
                            block_index=block_index,
                            block_type="paragraph",
                            raw_content=text,
                            normalized_content=text,
                            position=BlockPosition(
                                page_number=page.page_number,
                                char_start=0,
                                char_end=len(text),
                            ),
                        )
                    )
                    block_index += 1
        except Exception as exc:
            warnings.append(
                ParserWarning(
                    code="PDF_PARSE_ERROR",
                    message=f"pdfplumber failed: {exc}",
                )
            )

        raw_text = "\n\n".join(raw_text_parts)
        if not raw_text and not warnings:
            warnings.append(
                ParserWarning(code="PARSER_OUTPUT_EMPTY", message="No PDF text content extracted.")
            )

        return ParserResult(
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            raw_text=raw_text,
            blocks=blocks,
            metadata={"filename": filename, "page_count": page_count},
            warnings=warnings,
        )
