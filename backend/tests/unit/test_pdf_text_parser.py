from unittest.mock import MagicMock, patch

from app.providers.parsers.pdf_text_parser import PdfTextParser


def test_pdf_text_parser_extracts_text_with_pdfplumber() -> None:
    parser = PdfTextParser()

    mock_page = MagicMock()
    mock_page.page_number = 1
    mock_page.extract_text.return_value = "Hello PDF 中文测试"

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__len__.return_value = 1

    with patch("app.providers.parsers.pdf_text_parser.pdfplumber") as mock_plumber:
        mock_plumber.open.return_value.__enter__.return_value = mock_pdf
        result = parser.parse(b"fake pdf bytes", filename="handbook.pdf")

    assert result.parser_name == "pdf_text_parser"
    assert result.raw_text == "Hello PDF 中文测试"
    assert result.metadata["page_count"] == 1
    assert result.blocks[0].block_type == "paragraph"
    assert result.blocks[0].position.page_number == 1
    assert result.blocks[0].raw_content == "Hello PDF 中文测试"


def test_pdf_text_parser_handles_empty_pages() -> None:
    parser = PdfTextParser()

    mock_page = MagicMock()
    mock_page.page_number = 1
    mock_page.extract_text.return_value = "   "  # whitespace only

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__len__.return_value = 1

    with patch("app.providers.parsers.pdf_text_parser.pdfplumber") as mock_plumber:
        mock_plumber.open.return_value.__enter__.return_value = mock_pdf
        result = parser.parse(b"empty", filename="empty.pdf")

    assert result.raw_text == ""
    assert len(result.blocks) == 0
    assert any(w.code == "PARSER_OUTPUT_EMPTY" for w in result.warnings)
