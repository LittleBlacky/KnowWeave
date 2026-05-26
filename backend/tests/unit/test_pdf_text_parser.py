from app.providers.parsers.pdf_text_parser import PdfTextParser


def test_pdf_text_parser_extracts_simple_text_stream_blocks() -> None:
    parser = PdfTextParser()
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nstream\nBT (Hello PDF) Tj ET\nendstream\nendobj\n%%EOF"

    result = parser.parse(pdf_bytes, filename="handbook.pdf")

    assert result.parser_name == "pdf_text_parser"
    assert result.raw_text == "Hello PDF"
    assert result.metadata["page_count"] == 1
    assert result.blocks[0].block_type == "paragraph"
    assert result.blocks[0].position.page_number == 1
    assert result.blocks[0].raw_content == "Hello PDF"
