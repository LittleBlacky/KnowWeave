from app.providers.parsers.markdown_parser import MarkdownParser


def test_markdown_parser_detects_headings_lists_and_code_blocks() -> None:
    parser = MarkdownParser()
    content = b"# Handbook\n\n- Keep citations\n- Review chunks\n\n```python\nprint('ok')\n```"

    result = parser.parse(content, filename="handbook.md")

    assert result.parser_name == "markdown_parser"
    assert [block.block_type for block in result.blocks] == ["heading", "list", "code"]
    assert result.blocks[0].raw_content == "# Handbook"
    assert result.blocks[0].metadata == {"heading_level": 1}
    assert result.blocks[1].raw_content == "- Keep citations\n- Review chunks"
    assert result.blocks[2].raw_content == "```python\nprint('ok')\n```"


def test_markdown_parser_preserves_tables_as_placeholder_blocks() -> None:
    parser = MarkdownParser()
    content = b"| Name | Owner |\n| --- | --- |\n| Policy | Ops |"

    result = parser.parse(content, filename="table.md")

    assert [block.block_type for block in result.blocks] == ["table"]
    assert result.blocks[0].metadata == {"is_placeholder": True}
    assert result.blocks[0].raw_content == "| Name | Owner |\n| --- | --- |\n| Policy | Ops |"
    assert [warning.code for warning in result.warnings] == ["TABLE_AS_PLACEHOLDER"]
