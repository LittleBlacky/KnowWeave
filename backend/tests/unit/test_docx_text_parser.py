from __future__ import annotations

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from app.providers.parsers.docx_text_parser import DocxTextParser


def _docx_bytes(document_xml: str) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", document_xml)
    return buffer.getvalue()


def test_docx_text_parser_extracts_paragraph_blocks() -> None:
    parser = DocxTextParser()
    content = _docx_bytes(
        """
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:body>
            <w:p><w:r><w:t>Executive Handbook</w:t></w:r></w:p>
            <w:p><w:r><w:t>Use traceable citations.</w:t></w:r></w:p>
          </w:body>
        </w:document>
        """
    )

    result = parser.parse(content, filename="handbook.docx")

    assert result.parser_name == "docx_text_parser"
    assert result.raw_text == "Executive Handbook\nUse traceable citations."
    assert [block.raw_content for block in result.blocks] == [
        "Executive Handbook",
        "Use traceable citations.",
    ]
    assert result.blocks[1].metadata == {"paragraph_index": 1}


def test_docx_text_parser_preserves_tables_as_placeholder_blocks() -> None:
    parser = DocxTextParser()
    content = _docx_bytes(
        """
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:body>
            <w:tbl>
              <w:tr>
                <w:tc><w:p><w:r><w:t>Name</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>Owner</w:t></w:r></w:p></w:tc>
              </w:tr>
              <w:tr>
                <w:tc><w:p><w:r><w:t>Policy</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>Ops</w:t></w:r></w:p></w:tc>
              </w:tr>
            </w:tbl>
          </w:body>
        </w:document>
        """
    )

    result = parser.parse(content, filename="table.docx")

    assert [block.block_type for block in result.blocks] == ["table"]
    assert result.blocks[0].raw_content == "Name | Owner\nPolicy | Ops"
    assert result.blocks[0].metadata == {"is_placeholder": True}
    assert [warning.code for warning in result.warnings] == ["TABLE_AS_PLACEHOLDER"]
