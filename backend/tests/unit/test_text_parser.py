from app.providers.parsers.text_parser import TextParser


def test_text_parser_splits_paragraphs_with_line_positions() -> None:
    parser = TextParser()

    result = parser.parse(b"Intro line\n\nSecond paragraph\nwith continuation", filename="notes.txt")

    assert result.parser_name == "text_parser"
    assert result.parser_version == "0.1.0"
    assert result.raw_text == "Intro line\n\nSecond paragraph\nwith continuation"
    assert [block.block_type for block in result.blocks] == ["paragraph", "paragraph"]
    assert result.blocks[0].raw_content == "Intro line"
    assert result.blocks[0].position.line_start == 1
    assert result.blocks[0].position.line_end == 1
    assert result.blocks[1].raw_content == "Second paragraph\nwith continuation"
    assert result.blocks[1].position.line_start == 3
    assert result.blocks[1].position.line_end == 4
