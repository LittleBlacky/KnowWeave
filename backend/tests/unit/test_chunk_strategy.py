from __future__ import annotations

from uuid import uuid4

from app.services.chunk_strategy import BlockForChunking, ChunkStrategyOptions, build_chunk_candidates


def test_chunk_strategy_merges_short_adjacent_text_blocks_with_locator() -> None:
    first_block_id = uuid4()
    second_block_id = uuid4()

    chunks = build_chunk_candidates(
        [
            BlockForChunking(
                block_id=first_block_id,
                block_type="heading",
                raw_content="# Policy",
                line_start=1,
                line_end=1,
            ),
            BlockForChunking(
                block_id=second_block_id,
                block_type="paragraph",
                raw_content="Leave requests require manager approval.",
                line_start=3,
                line_end=3,
            ),
        ],
        options=ChunkStrategyOptions(min_chars=80),
    )

    assert len(chunks) == 1
    assert chunks[0].raw_content == "# Policy\n\nLeave requests require manager approval."
    assert chunks[0].chunk_type == "text"
    assert chunks[0].source.block_id == first_block_id
    assert chunks[0].source.line_start == 1
    assert chunks[0].source.line_end == 3


def test_chunk_strategy_splits_long_blocks_and_preserves_page_locator() -> None:
    block_id = uuid4()

    chunks = build_chunk_candidates(
        [
            BlockForChunking(
                block_id=block_id,
                block_type="paragraph",
                raw_content="Alpha. Beta. Gamma. Delta.",
                page_number=2,
                char_start=10,
                char_end=36,
            )
        ],
        options=ChunkStrategyOptions(max_chars=13, min_chars=1, overlap_chars=0),
    )

    assert [chunk.raw_content for chunk in chunks] == ["Alpha. Beta.", "Gamma. Delta."]
    assert [chunk.source.page_number for chunk in chunks] == [2, 2]
    assert [chunk.source.block_id for chunk in chunks] == [block_id, block_id]
