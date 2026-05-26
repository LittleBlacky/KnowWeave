from __future__ import annotations

from io import BytesIO
from zipfile import BadZipFile, ZipFile
import xml.etree.ElementTree as ET

from app.providers.parsers.base import BlockPosition, ParsedBlock, ParserResult, ParserWarning

WORD_NAMESPACE = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class DocxTextParser:
    parser_name = "docx_text_parser"
    parser_version = "0.1.0"

    def parse(self, content: bytes, *, filename: str) -> ParserResult:
        warnings: list[ParserWarning] = []
        parsed_blocks: list[ParsedBlock] = []
        try:
            with ZipFile(BytesIO(content)) as archive:
                document_xml = archive.read("word/document.xml")
        except (BadZipFile, KeyError):
            document_xml = b""
            warnings.append(ParserWarning(code="DOCX_READ_FAILED", message="Could not read word/document.xml."))

        if document_xml:
            root = ET.fromstring(document_xml)
            paragraph_index = 0
            for child in root.iter():
                if child.tag == f"{WORD_NAMESPACE}tbl":
                    rows = []
                    for row in child.iter(f"{WORD_NAMESPACE}tr"):
                        cells = []
                        for cell in row.iter(f"{WORD_NAMESPACE}tc"):
                            cell_text = " ".join(
                                text_node.text or "" for text_node in cell.iter(f"{WORD_NAMESPACE}t")
                            ).strip()
                            cells.append(cell_text)
                        if any(cells):
                            rows.append(" | ".join(cells))
                    if rows:
                        parsed_blocks.append(
                            ParsedBlock(
                                block_index=len(parsed_blocks),
                                block_type="table",
                                raw_content="\n".join(rows),
                                normalized_content="\n".join(rows),
                                position=BlockPosition(char_start=None, char_end=None),
                                metadata={"is_placeholder": True},
                            )
                        )
                    continue

                if child.tag != f"{WORD_NAMESPACE}p" or _has_table_ancestor(child, root):
                    continue

                text = "".join(node.text or "" for node in child.iter(f"{WORD_NAMESPACE}t")).strip()
                if text:
                    parsed_blocks.append(
                        ParsedBlock(
                            block_index=len(parsed_blocks),
                            block_type="paragraph",
                            raw_content=text,
                            normalized_content=text,
                            position=BlockPosition(char_start=None, char_end=None),
                            metadata={"paragraph_index": paragraph_index},
                        )
                    )
                    paragraph_index += 1

        raw_text = "\n".join(block.raw_content for block in parsed_blocks)
        if any(block.block_type == "table" for block in parsed_blocks):
            warnings.append(
                ParserWarning(
                    code="TABLE_AS_PLACEHOLDER",
                    message="DOCX tables were preserved as placeholder blocks.",
                )
            )
        if not raw_text:
            warnings.append(ParserWarning(code="PARSER_OUTPUT_EMPTY", message="No DOCX text content extracted."))
        return ParserResult(
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            raw_text=raw_text,
            blocks=parsed_blocks,
            metadata={
                "filename": filename,
                "paragraph_count": sum(block.block_type == "paragraph" for block in parsed_blocks),
            },
            warnings=warnings,
        )


def _has_table_ancestor(element: ET.Element, root: ET.Element) -> bool:
    for table in root.iter(f"{WORD_NAMESPACE}tbl"):
        if element is not table and any(descendant is element for descendant in table.iter()):
            return True
    return False
