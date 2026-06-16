"""Tests for the ExtractionProvider."""

from __future__ import annotations

import pytest

from app.models.files import Chunk
from app.models.knowledge import KnowledgeUnit
from app.providers.extraction import ExtractionCandidate, ExtractionError, ExtractionProvider, ExtractionResult
from app.providers.fake_llm import FakeLLMProvider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chunk(
    *,
    chunk_id: str = "00000000-0000-0000-0000-000000000001",
    file_id: str = "00000000-0000-0000-0000-000000000002",
    raw_content: str = "All access requests shall require manager approval before provisioning.",
    chunk_type: str = "text",
    chunk_index: int = 0,
) -> Chunk:
    from uuid import UUID

    return Chunk(
        id=UUID(chunk_id),
        file_id=UUID(file_id),
        parse_result_id=UUID("00000000-0000-0000-0000-000000000003"),
        chunk_index=chunk_index,
        chunk_type=chunk_type,
        raw_content=raw_content,
        edited_content=None,
        is_manually_edited=False,
        status="draft",
        quality_signals=[],
        char_count=len(raw_content),
        search_text=raw_content,
        is_searchable=True,
        metadata_={},
    )


def _make_knowledge_unit(
    *,
    unit_id: str = "00000000-0000-0000-0000-000000000010",
    title: str = "Access request approval",
    summary: str = "Manager approval required",
    unit_type: str = "rule",
) -> KnowledgeUnit:
    from uuid import UUID

    return KnowledgeUnit(
        id=UUID(unit_id),
        title=title,
        unit_type=unit_type,
        content="All access requests require manager approval.",
        summary=summary,
        status="draft",
        created_from="manual",
        search_text=f"{title}\n{summary}",
        metadata_={},
    )


# ---------------------------------------------------------------------------
# _parse_response
# ---------------------------------------------------------------------------


class TestParseResponse:
    def test_parses_valid_json_array(self) -> None:
        raw = """
[
  {"title": "Access Rule", "unit_type": "rule", "content": "Managers must approve.", "summary": "Approval by manager.", "source_chunk_index": 0}
]
"""
        candidates = ExtractionProvider._parse_response(raw, batch_size=3)
        assert len(candidates) == 1
        assert candidates[0].title == "Access Rule"
        assert candidates[0].unit_type == "rule"

    def test_strips_markdown_code_fence(self) -> None:
        raw = """```json
[{"title": "X", "unit_type": "concept", "content": "Y", "summary": "Z", "source_chunk_index": 0}]
```"""
        candidates = ExtractionProvider._parse_response(raw, batch_size=1)
        assert len(candidates) == 1
        assert candidates[0].title == "X"

    def test_skips_items_without_title(self) -> None:
        raw = '[{"unit_type": "rule", "content": "Y", "summary": "Z", "source_chunk_index": 0}]'
        candidates = ExtractionProvider._parse_response(raw, batch_size=1)
        assert len(candidates) == 0

    def test_validates_unit_type(self) -> None:
        raw = '[{"title": "X", "unit_type": "INVALID", "content": "Y", "summary": "Z", "source_chunk_index": 0}]'
        candidates = ExtractionProvider._parse_response(raw, batch_size=1)
        assert len(candidates) == 1
        assert candidates[0].unit_type == "concept"  # fallback to default

    def test_rejects_out_of_range_chunk_index(self) -> None:
        raw = '[{"title": "X", "unit_type": "fact", "content": "Y", "summary": "Z", "source_chunk_index": 99}]'
        candidates = ExtractionProvider._parse_response(raw, batch_size=3)
        assert len(candidates) == 0

    def test_raises_on_non_json_response(self) -> None:
        with pytest.raises(ExtractionError, match="JSON array"):
            ExtractionProvider._parse_response("This is not JSON at all.", batch_size=1)


# ---------------------------------------------------------------------------
# Extract (integration with FakeLLMProvider)
# ---------------------------------------------------------------------------


class TestExtractWithFakeProvider:
    @pytest.mark.asyncio
    async def test_extract_with_fake_provider_handles_non_json_response(self) -> None:
        """FakeLLMProvider returns plain text, not JSON — extraction should raise ExtractionError."""
        provider = ExtractionProvider(llm_provider=FakeLLMProvider())
        chunks = [_make_chunk(raw_content="System access needs IT manager approval and a ticket ID.")]
        # FakeLLMProvider returns "Fake answer: ..." which is not valid JSON.
        # This is expected behaviour — the extraction provider correctly raises.
        with pytest.raises(ExtractionError, match="JSON"):
            await provider.extract(chunks=chunks, existing_kus=[])

    @pytest.mark.asyncio
    async def test_extract_empty_chunks_returns_empty(self) -> None:
        provider = ExtractionProvider(llm_provider=FakeLLMProvider())
        result = await provider.extract(chunks=[], existing_kus=[])
        assert result.candidates == []


# ---------------------------------------------------------------------------
# check_duplicate
# ---------------------------------------------------------------------------


class TestCheckDuplicate:
    @pytest.mark.asyncio
    async def test_no_existing_kus_returns_false(self) -> None:
        provider = ExtractionProvider(llm_provider=FakeLLMProvider())
        candidate = ExtractionCandidate(
            title="Leave rule",
            unit_type="rule",
            content="Leave requires approval.",
            summary="Approval needed.",
            source_chunk_index=0,
        )
        is_dup = await provider.check_duplicate(candidate=candidate, existing_kus=[])
        assert is_dup is False

    @pytest.mark.asyncio
    async def test_with_existing_kus_calls_llm(self) -> None:
        provider = ExtractionProvider(llm_provider=FakeLLMProvider())
        candidate = ExtractionCandidate(
            title="Leave rule",
            unit_type="rule",
            content="Leave requires approval.",
            summary="Approval needed.",
            source_chunk_index=0,
        )
        existing = [_make_knowledge_unit(title="Leave approval", summary="Manager must approve leave")]
        # Fake provider may return true or false; just ensure no crash
        is_dup = await provider.check_duplicate(candidate=candidate, existing_kus=existing)
        assert isinstance(is_dup, bool)
