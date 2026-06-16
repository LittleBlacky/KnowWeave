from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.base import utcnow
from app.models.files import Chunk, KnowledgeFile, SourceSpan
from app.models.knowledge import KnowledgeUnit, KnowledgeUnitSource, Tag, TagBinding
from app.providers.base import LLMProvider
from app.providers.extraction import ExtractionCandidate, ExtractionError, ExtractionProvider
from app.providers.factory import build_default_llm_provider
from app.services.tag_service import TagService


class KnowledgeUnitNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="KNOWLEDGE_UNIT_NOT_FOUND",
            message="Knowledge Unit not found.",
            status_code=404,
        )


class KnowledgeUnitChunkNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="KNOWLEDGE_UNIT_SOURCE_CHUNK_NOT_FOUND",
            message="Knowledge Unit source chunk was not found.",
            status_code=404,
        )


class KnowledgeUnitVerifiedSourceRequiredError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="KNOWLEDGE_UNIT_VERIFIED_SOURCE_REQUIRED",
            message="Verified Knowledge Units require at least one explainable source.",
            status_code=400,
        )


class KnowledgeUnitService:
    def __init__(self, *, session: Session, llm_provider: LLMProvider | None = None) -> None:
        self.session = session
        self._llm = llm_provider or build_default_llm_provider(get_settings())

    def create_knowledge_unit(
        self,
        *,
        title: str,
        content: str,
        unit_type: str = "concept",
        summary: str | None = None,
        status: str = "draft",
        applicable_scope: str | None = None,
        source_chunk_ids: list[UUID] | None = None,
        tag_ids: list[UUID] | None = None,
    ) -> KnowledgeUnit:
        source_chunk_ids = source_chunk_ids or []
        tag_ids = tag_ids or []
        self._validate_verified_source(status=status, source_chunk_ids=source_chunk_ids)

        now = utcnow()
        unit = KnowledgeUnit(
            title=title,
            unit_type=unit_type,
            content=content,
            summary=summary,
            status=status,
            applicable_scope=applicable_scope,
            created_from="chunk" if source_chunk_ids else "manual",
            search_text=self._search_text(title=title, summary=summary, content=content),
            metadata_={},
            verified_at=now if status == "verified" else None,
            archived_at=now if status == "archived" else None,
        )
        self.session.add(unit)
        self.session.flush()

        self._replace_sources(unit.id, source_chunk_ids)
        self._replace_tags(unit.id, tag_ids)
        self.session.commit()
        self.session.refresh(unit)
        return unit

    async def auto_generate_from_chunks(
        self,
        file_id: UUID,
        *,
        batch_size: int = 6,
    ) -> dict:
        """Extract Knowledge Units from file chunks using LLM.

        Batches chunks, calls the extraction provider, deduplicates against
        existing KUs, and persists the results as draft Knowledge Units.

        Returns a summary dict with counts and the new KU objects.
        """
        file_record = self.session.get(KnowledgeFile, file_id)
        if file_record is None:
            raise KnowledgeUnitNotFoundError()

        chunks = self._get_searchable_chunks(file_id)
        if not chunks:
            return {"extracted": 0, "skipped_duplicates": 0, "units": []}

        existing_kus = self._get_existing_kus_for_file(file_id)
        extraction = ExtractionProvider(llm_provider=self._llm)

        all_candidates: list[tuple[ExtractionCandidate, Chunk]] = []
        batches = list(_batch_list(chunks, batch_size))
        accumulated_kus = list(existing_kus)  # grow as we extract to avoid intra-batch dupes

        for batch in batches:
            try:
                result = await extraction.extract(
                    chunks=batch,
                    existing_kus=accumulated_kus,
                )
            except ExtractionError:
                # If one batch fails, skip it and continue with the rest.
                continue

            for candidate in result.candidates:
                if candidate.source_chunk_index >= len(batch):
                    continue
                source_chunk = batch[candidate.source_chunk_index]

                # LLM-based dedup check against existing + already-extracted KUs
                try:
                    is_dup = await extraction.check_duplicate(
                        candidate=candidate,
                        existing_kus=accumulated_kus,
                    )
                except ExtractionError:
                    is_dup = False  # fail-open: accept the candidate

                if not is_dup:
                    all_candidates.append((candidate, source_chunk))
                    # Track in accumulated list so subsequent batches can dedup
                    accumulated_kus.append(
                        KnowledgeUnit(
                            title=candidate.title,
                            summary=candidate.summary,
                            unit_type=candidate.unit_type,
                            content="",
                            status="draft",
                            created_from="ai_extracted",
                            search_text="",
                            metadata_={},
                        )
                    )

        # Persist extracted candidates
        new_units: list[KnowledgeUnit] = []
        for candidate, source_chunk in all_candidates:
            unit = self.create_knowledge_unit(
                title=candidate.title,
                content=candidate.content,
                unit_type=candidate.unit_type,
                summary=candidate.summary,
                status="draft",
                source_chunk_ids=[source_chunk.id],
            )
            new_units.append(unit)

        return {
            "extracted": len(new_units),
            "skipped_duplicates": len(all_candidates) - len(new_units),
            "units": new_units,
        }

    def batch_update_status(
        self,
        *,
        unit_ids: list[UUID],
        status: str,
    ) -> int:
        """Batch-update status for multiple Knowledge Units.

        Returns the count of units actually updated.
        """
        if status not in ("verified", "archived", "draft", "needs_review"):
            raise AppError(
                code="INVALID_STATUS",
                message=f"Status '{status}' is not valid for batch update.",
                status_code=400,
            )
        if not unit_ids:
            return 0

        updated = 0
        for uid in unit_ids:
            unit = self.session.get(KnowledgeUnit, uid)
            if unit is None:
                continue
            unit.status = status
            if status == "verified":
                unit.verified_at = utcnow()
            if status == "archived":
                unit.archived_at = utcnow()
            self.session.add(unit)
            updated += 1
        self.session.commit()
        return updated

    def _get_searchable_chunks(self, file_id: UUID) -> list[Chunk]:
        statement = (
            select(Chunk)
            .where(Chunk.file_id == file_id)
            .where(Chunk.is_searchable.is_(True))
            .order_by(Chunk.chunk_index.asc())
        )
        return list(self.session.scalars(statement).all())

    def _get_existing_kus_for_file(self, file_id: UUID) -> list[KnowledgeUnit]:
        statement = (
            select(KnowledgeUnit)
            .join(KnowledgeUnitSource, KnowledgeUnitSource.knowledge_unit_id == KnowledgeUnit.id)
            .where(KnowledgeUnitSource.file_id == file_id)
            .order_by(KnowledgeUnit.created_at.desc())
        )
        return list(self.session.scalars(statement).all())

    def merge_knowledge_units(self, *, source_ids: list[UUID], title: str) -> KnowledgeUnit:
        """Merge multiple Knowledge Units into one, combining content and sources."""
        if len(source_ids) < 2:
            raise AppError(
                code="MERGE_REQUIRES_MULTIPLE",
                message="At least two Knowledge Units are required for a merge.",
                status_code=400,
            )

        source_units = [self.get_knowledge_unit(uid) for uid in source_ids]
        # Collect all source chunks from merged units
        all_chunk_ids: list[UUID] = []
        combined_content_parts: list[str] = []
        for unit in source_units:
            combined_content_parts.append(f"## {unit.title}\n{unit.content}")
            for src in self.list_sources(unit.id):
                if src.chunk_id is not None and src.chunk_id not in all_chunk_ids:
                    all_chunk_ids.append(src.chunk_id)

        merged = self.create_knowledge_unit(
            title=title,
            content="\n\n".join(combined_content_parts),
            unit_type="concept",
            summary=f"Merged from {len(source_units)} units: {', '.join(u.title for u in source_units)}"[:200],
            status="draft",
            source_chunk_ids=all_chunk_ids,
        )

        # Archive the source units
        for unit in source_units:
            unit.status = "archived"
            unit.archived_at = utcnow()
            self.session.add(unit)

        self.session.commit()
        self.session.refresh(merged)
        return merged

    def split_knowledge_unit(
        self, *, source_id: UUID, titles: list[str], content_splits: list[str]
    ) -> list[KnowledgeUnit]:
        """Split a long Knowledge Unit into multiple smaller units."""
        if len(titles) != len(content_splits) or len(titles) < 2:
            raise AppError(
                code="SPLIT_REQUIRES_VALID_PARTS",
                message="Split requires at least 2 parts with matching titles and content.",
                status_code=400,
            )

        source = self.get_knowledge_unit(source_id)
        source_chunk_ids = [s.chunk_id for s in self.list_sources(source.id) if s.chunk_id is not None]

        created: list[KnowledgeUnit] = []
        for title, content in zip(titles, content_splits):
            unit = self.create_knowledge_unit(
                title=title,
                content=content,
                unit_type=source.unit_type,
                summary=content[:200],
                status="draft",
                source_chunk_ids=source_chunk_ids,
            )
            created.append(unit)

        # Archive the original
        source.status = "archived"
        source.archived_at = utcnow()
        self.session.add(source)
        self.session.commit()

        return created

    def list_knowledge_units(
        self,
        *,
        status: str | None = None,
        tag: str | None = None,
        source_file_id: UUID | None = None,
        unit_type: str | None = None,
    ) -> list[KnowledgeUnit]:
        statement = select(KnowledgeUnit)
        if status is not None:
            statement = statement.where(KnowledgeUnit.status == status)
        if unit_type is not None:
            statement = statement.where(KnowledgeUnit.unit_type == unit_type)
        if source_file_id is not None:
            statement = statement.join(
                KnowledgeUnitSource,
                KnowledgeUnitSource.knowledge_unit_id == KnowledgeUnit.id,
            ).where(KnowledgeUnitSource.file_id == source_file_id)
        if tag is not None:
            statement = (
                statement.join(
                    TagBinding,
                    (TagBinding.target_type == "knowledge_unit")
                    & (TagBinding.target_id == KnowledgeUnit.id),
                )
                .join(Tag, Tag.id == TagBinding.tag_id)
                .where(Tag.name == tag)
            )
        statement = statement.order_by(KnowledgeUnit.updated_at.desc()).distinct(KnowledgeUnit.id)
        return list(self.session.scalars(statement).all())

    def get_knowledge_unit(self, knowledge_unit_id: UUID) -> KnowledgeUnit:
        unit = self.session.get(KnowledgeUnit, knowledge_unit_id)
        if unit is None:
            raise KnowledgeUnitNotFoundError()
        return unit

    def update_knowledge_unit(
        self,
        knowledge_unit_id: UUID,
        *,
        title: str | None = None,
        content: str | None = None,
        unit_type: str | None = None,
        summary: str | None = None,
        status: str | None = None,
        applicable_scope: str | None = None,
        source_chunk_ids: list[UUID] | None = None,
        tag_ids: list[UUID] | None = None,
    ) -> KnowledgeUnit:
        unit = self.get_knowledge_unit(knowledge_unit_id)
        next_status = status or unit.status
        next_source_count = len(source_chunk_ids) if source_chunk_ids is not None else len(
            self.list_sources(unit.id)
        )
        if next_status == "verified" and next_source_count == 0:
            raise KnowledgeUnitVerifiedSourceRequiredError()

        if title is not None:
            unit.title = title
        if content is not None:
            unit.content = content
        if unit_type is not None:
            unit.unit_type = unit_type
        if summary is not None:
            unit.summary = summary
        if applicable_scope is not None:
            unit.applicable_scope = applicable_scope
        if status is not None:
            unit.status = status
            if status == "verified":
                unit.verified_at = utcnow()
            if status == "archived":
                unit.archived_at = utcnow()
        unit.search_text = self._search_text(
            title=unit.title,
            summary=unit.summary,
            content=unit.content,
        )
        self.session.add(unit)
        self.session.flush()

        if source_chunk_ids is not None:
            self._replace_sources(unit.id, source_chunk_ids)
            unit.created_from = "chunk" if source_chunk_ids else "manual"
        if tag_ids is not None:
            self._replace_tags(unit.id, tag_ids)

        self.session.commit()
        self.session.refresh(unit)
        return unit

    def list_sources(self, knowledge_unit_id: UUID) -> list[KnowledgeUnitSource]:
        self.get_knowledge_unit(knowledge_unit_id)
        statement = (
            select(KnowledgeUnitSource)
            .where(KnowledgeUnitSource.knowledge_unit_id == knowledge_unit_id)
            .order_by(KnowledgeUnitSource.created_at.asc())
        )
        return list(self.session.scalars(statement).all())

    def list_tags(self, knowledge_unit_id: UUID) -> list[Tag]:
        self.get_knowledge_unit(knowledge_unit_id)
        return TagService(session=self.session).tags_for_target(
            target_type="knowledge_unit",
            target_id=knowledge_unit_id,
        )

    def _replace_sources(self, knowledge_unit_id: UUID, source_chunk_ids: list[UUID]) -> None:
        self.session.execute(
            delete(KnowledgeUnitSource).where(
                KnowledgeUnitSource.knowledge_unit_id == knowledge_unit_id
            )
        )
        for index, chunk_id in enumerate(source_chunk_ids, start=1):
            chunk = self.session.get(Chunk, chunk_id)
            if chunk is None:
                raise KnowledgeUnitChunkNotFoundError()
            file_record = self.session.get(KnowledgeFile, chunk.file_id)
            source_span = self._source_span_for_chunk(chunk.id)
            self.session.add(
                KnowledgeUnitSource(
                    knowledge_unit_id=knowledge_unit_id,
                    file_id=chunk.file_id,
                    chunk_id=chunk.id,
                    source_span_id=source_span.id if source_span is not None else None,
                    source_type="chunk",
                    source_label=f"S{index}",
                    source_available=file_record is not None and file_record.deleted_at is None,
                    created_at=utcnow(),
                )
            )

    def _replace_tags(self, knowledge_unit_id: UUID, tag_ids: list[UUID]) -> None:
        TagService(session=self.session).replace_target_tags(
            target_type="knowledge_unit",
            target_id=knowledge_unit_id,
            tag_ids=tag_ids,
        )

    def _source_span_for_chunk(self, chunk_id: UUID) -> SourceSpan | None:
        statement = select(SourceSpan).where(SourceSpan.chunk_id == chunk_id).limit(1)
        return self.session.scalar(statement)

    def _validate_verified_source(self, *, status: str, source_chunk_ids: list[UUID]) -> None:
        if status == "verified" and not source_chunk_ids:
            raise KnowledgeUnitVerifiedSourceRequiredError()

    def _search_text(self, *, title: str, summary: str | None, content: str) -> str:
        parts = [title]
        if summary:
            parts.append(summary)
        parts.append(content)
        return "\n".join(parts)


def _batch_list(items: list, batch_size: int) -> list[list]:
    """Split *items* into sub-lists of at most *batch_size* elements."""
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]
