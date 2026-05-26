from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.base import utcnow
from app.models.chat import RetrievedContext
from app.models.files import Chunk, KnowledgeFile, ParseResult, SourceSpan
from app.models.knowledge import KnowledgeUnit, KnowledgeUnitSource
from app.models.wiki import WikiPage
from app.services.index_service import IndexService


@dataclass
class SearchResultItem:
    result_id: UUID
    result_type: str
    title: str
    preview_text: str
    score: Decimal
    rank: int
    source: dict[str, object]
    status: dict[str, object]
    metadata: dict[str, object]


@dataclass(frozen=True)
class SearchResponse:
    retrieval_run_id: UUID
    query: str
    strategy: str
    results: list[SearchResultItem]


class RetrievalRunNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="RETRIEVAL_RUN_NOT_FOUND",
            message="Retrieval run not found.",
            status_code=404,
        )


class SearchService:
    def __init__(self, *, session: Session, index: IndexService | None = None) -> None:
        self.session = session
        self.index = index or IndexService(session=session)

    def search(
        self,
        *,
        query: str,
        top_k: int = 10,
        target_types: list[str] | None = None,
    ) -> SearchResponse:
        retrieval_run_id = uuid4()
        requested_target_types = self._normalize_target_types(target_types)
        results = self._search_targets(
            query=query,
            top_k=top_k,
            target_types=requested_target_types,
        )
        for rank, result in enumerate(results, start=1):
            result.rank = rank
            self._persist_result_context(
                result,
                query=query,
                retrieval_run_id=retrieval_run_id,
                top_k=top_k,
                target_types=requested_target_types,
            )
        self.session.commit()
        return SearchResponse(
            retrieval_run_id=retrieval_run_id,
            query=query,
            strategy="keyword",
            results=results,
        )

    def get_retrieval_run(self, retrieval_run_id: UUID) -> SearchResponse:
        statement = (
            select(RetrievedContext)
            .where(RetrievedContext.retrieval_run_id == retrieval_run_id)
            .order_by(RetrievedContext.rank.asc())
        )
        contexts = list(self.session.scalars(statement).all())
        if not contexts:
            raise RetrievalRunNotFoundError()

        results: list[SearchResultItem] = []
        for context in contexts:
            item = self._result_from_context(context)
            if item is None:
                continue
            results.append(item)

        return SearchResponse(
            retrieval_run_id=retrieval_run_id,
            query=contexts[0].query_text,
            strategy=contexts[0].retrieval_strategy,
            results=results,
        )

    def _search_targets(
        self,
        *,
        query: str,
        top_k: int,
        target_types: list[str],
    ) -> list[SearchResultItem]:
        results: list[SearchResultItem] = []
        if "chunk" in target_types:
            results.extend(
                self._chunk_result_item(chunk, query=query)
                for chunk in self.index.search_chunks(query=query, top_k=top_k)
            )
        if "file" in target_types:
            results.extend(
                self._file_result_item(file_record, query=query)
                for file_record in self._search_files(query=query, top_k=top_k)
            )
        if "knowledge_unit" in target_types:
            results.extend(
                self._knowledge_unit_result_item(unit, query=query)
                for unit in self._search_knowledge_units(query=query, top_k=top_k)
            )
        if "wiki_page" in target_types:
            results.extend(
                self._wiki_page_result_item(wiki, query=query)
                for wiki in self._search_wiki_pages(query=query, top_k=top_k)
            )

        return sorted(results, key=lambda item: (-item.score, item.result_type, item.title))[:top_k]

    def _persist_result_context(
        self,
        item: SearchResultItem,
        *,
        query: str,
        retrieval_run_id: UUID,
        top_k: int,
        target_types: list[str],
    ) -> None:
        self.session.add(
            RetrievedContext(
                retrieval_run_id=retrieval_run_id,
                chat_message_id=None,
                query_text=query,
                result_type=item.result_type,
                result_id=item.result_id,
                rank=item.rank,
                score=item.score,
                retrieval_strategy="keyword",
                retrieval_params={"top_k": top_k, "target_types": target_types},
                used_in_answer=False,
                created_at=utcnow(),
            )
        )

    def _result_from_context(self, context: RetrievedContext) -> SearchResultItem | None:
        if context.result_type == "chunk":
            chunk = self.session.get(Chunk, context.result_id)
            return (
                self._chunk_result_item(
                    chunk,
                    rank=context.rank,
                    score=context.score or Decimal("0.0000"),
                )
                if chunk is not None
                else None
            )
        if context.result_type == "file":
            file_record = self.session.get(KnowledgeFile, context.result_id)
            return (
                self._file_result_item(
                    file_record,
                    query=context.query_text,
                    rank=context.rank,
                    score=context.score or Decimal("0.0000"),
                )
                if file_record is not None
                else None
            )
        if context.result_type == "knowledge_unit":
            unit = self.session.get(KnowledgeUnit, context.result_id)
            return (
                self._knowledge_unit_result_item(
                    unit,
                    query=context.query_text,
                    rank=context.rank,
                    score=context.score or Decimal("0.0000"),
                )
                if unit is not None
                else None
            )
        if context.result_type == "wiki_page":
            wiki = self.session.get(WikiPage, context.result_id)
            return (
                self._wiki_page_result_item(
                    wiki,
                    query=context.query_text,
                    rank=context.rank,
                    score=context.score or Decimal("0.0000"),
                )
                if wiki is not None
                else None
            )
        return None

    def _chunk_result_item(
        self,
        chunk: Chunk,
        *,
        rank: int = 0,
        score: Decimal | None = None,
        query: str | None = None,
    ) -> SearchResultItem:
        file_record = self.session.get(KnowledgeFile, chunk.file_id)
        source_span = self._source_span_for_chunk(chunk.id)
        preview_text = chunk.edited_content or chunk.raw_content
        return SearchResultItem(
            result_id=chunk.id,
            result_type="chunk",
            title=file_record.name if file_record is not None else "Chunk",
            preview_text=preview_text,
            score=score if score is not None else self._score_text(query or "", chunk.search_text),
            rank=rank,
            source={
                "file_id": str(chunk.file_id),
                "file_name": file_record.name if file_record is not None else None,
                "source_span_id": str(source_span.id) if source_span is not None else None,
                "page_number": source_span.page_number if source_span is not None else None,
                "line_start": source_span.line_start if source_span is not None else None,
                "line_end": source_span.line_end if source_span is not None else None,
                "source_available": file_record is not None and file_record.deleted_at is None,
            },
            status={
                "chunk_status": chunk.status,
                "source_file_deleted": file_record is None or file_record.deleted_at is not None,
            },
            metadata={
                "chunk_index": chunk.chunk_index,
                "retrieval_strategy": "keyword",
                "matched_fields": ["search_text"],
            },
        )

    def _file_result_item(
        self,
        file_record: KnowledgeFile,
        *,
        query: str,
        rank: int = 0,
        score: Decimal | None = None,
    ) -> SearchResultItem:
        return SearchResultItem(
            result_id=file_record.id,
            result_type="file",
            title=file_record.name,
            preview_text=file_record.original_filename,
            score=score if score is not None else self._score_text(
                query,
                f"{file_record.name}\n{file_record.original_filename}",
            ),
            rank=rank,
            source={
                "file_id": str(file_record.id),
                "file_name": file_record.name,
                "source_span_id": None,
                "page_number": None,
                "line_start": None,
                "line_end": None,
                "source_available": file_record.deleted_at is None,
            },
            status={
                "file_status": file_record.status,
                "source_file_deleted": file_record.deleted_at is not None,
            },
            metadata={
                "file_type": file_record.file_type,
                "mime_type": file_record.mime_type,
                "retrieval_strategy": "keyword",
                "matched_fields": ["name", "original_filename"],
            },
        )

    def _knowledge_unit_result_item(
        self,
        unit: KnowledgeUnit,
        *,
        query: str,
        rank: int = 0,
        score: Decimal | None = None,
    ) -> SearchResultItem:
        source = self._source_for_knowledge_unit(unit.id)
        file_record = (
            self.session.get(KnowledgeFile, source.file_id)
            if source and source.file_id
            else None
        )
        source_span = (
            self.session.get(SourceSpan, source.source_span_id)
            if source and source.source_span_id
            else None
        )
        return SearchResultItem(
            result_id=unit.id,
            result_type="knowledge_unit",
            title=unit.title,
            preview_text=unit.summary or unit.content,
            score=score if score is not None else self._score_text(query, unit.search_text),
            rank=rank,
            source={
                "file_id": str(source.file_id) if source and source.file_id else None,
                "file_name": file_record.name if file_record is not None else None,
                "source_span_id": str(source.source_span_id) if source and source.source_span_id else None,
                "page_number": source_span.page_number if source_span is not None else None,
                "line_start": source_span.line_start if source_span is not None else None,
                "line_end": source_span.line_end if source_span is not None else None,
                "source_available": source.source_available if source is not None else False,
            },
            status={
                "knowledge_unit_status": unit.status,
                "source_file_deleted": file_record is not None and file_record.deleted_at is not None,
            },
            metadata={
                "unit_type": unit.unit_type,
                "created_from": unit.created_from,
                "retrieval_strategy": "keyword",
                "matched_fields": ["search_text"],
            },
        )

    def _wiki_page_result_item(
        self,
        wiki: WikiPage,
        *,
        query: str,
        rank: int = 0,
        score: Decimal | None = None,
    ) -> SearchResultItem:
        file_record = self.session.get(KnowledgeFile, wiki.source_file_id) if wiki.source_file_id else None
        return SearchResultItem(
            result_id=wiki.id,
            result_type="wiki_page",
            title=wiki.title,
            preview_text=wiki.summary or wiki.content_markdown,
            score=score if score is not None else self._score_text(query, wiki.search_text),
            rank=rank,
            source={
                "file_id": str(wiki.source_file_id) if wiki.source_file_id else None,
                "file_name": file_record.name if file_record is not None else None,
                "source_span_id": None,
                "page_number": None,
                "line_start": None,
                "line_end": None,
                "source_available": file_record is None or file_record.deleted_at is None,
            },
            status={
                "wiki_status": wiki.status,
                "source_file_deleted": file_record is not None and file_record.deleted_at is not None,
            },
            metadata={
                "wiki_type": wiki.wiki_type,
                "retrieval_strategy": "keyword",
                "matched_fields": ["search_text"],
            },
        )

    def _search_files(self, *, query: str, top_k: int) -> list[KnowledgeFile]:
        normalized_query = query.strip().lower()
        if not normalized_query:
            return []

        statement = (
            select(KnowledgeFile)
            .outerjoin(ParseResult, ParseResult.file_id == KnowledgeFile.id)
            .where(KnowledgeFile.deleted_at.is_(None))
            .where(KnowledgeFile.status != "soft_deleted")
            .where(
                func.lower(KnowledgeFile.name).contains(normalized_query)
                | func.lower(KnowledgeFile.original_filename).contains(normalized_query)
                | func.lower(ParseResult.raw_text).contains(normalized_query)
            )
            .order_by(KnowledgeFile.created_at.asc())
            .distinct()
            .limit(top_k)
        )
        return list(self.session.scalars(statement).all())

    def _search_knowledge_units(self, *, query: str, top_k: int) -> list[KnowledgeUnit]:
        normalized_query = query.strip().lower()
        if not normalized_query:
            return []

        statement = (
            select(KnowledgeUnit)
            .where(KnowledgeUnit.status != "archived")
            .where(func.lower(KnowledgeUnit.search_text).contains(normalized_query))
            .order_by(KnowledgeUnit.updated_at.desc())
            .limit(top_k)
        )
        return list(self.session.scalars(statement).all())

    def _search_wiki_pages(self, *, query: str, top_k: int) -> list[WikiPage]:
        normalized_query = query.strip().lower()
        if not normalized_query:
            return []

        statement = (
            select(WikiPage)
            .where(func.lower(WikiPage.search_text).contains(normalized_query))
            .order_by(WikiPage.updated_at.desc())
            .limit(top_k)
        )
        return list(self.session.scalars(statement).all())

    def _source_span_for_chunk(self, chunk_id: UUID) -> SourceSpan | None:
        statement = select(SourceSpan).where(SourceSpan.chunk_id == chunk_id).limit(1)
        return self.session.scalar(statement)

    def _source_for_knowledge_unit(self, knowledge_unit_id: UUID) -> KnowledgeUnitSource | None:
        statement = (
            select(KnowledgeUnitSource)
            .where(KnowledgeUnitSource.knowledge_unit_id == knowledge_unit_id)
            .order_by(KnowledgeUnitSource.created_at.asc())
            .limit(1)
        )
        return self.session.scalar(statement)

    def _score_chunk(self, chunk: Chunk, query: str) -> Decimal:
        return self._score_text(query, chunk.search_text)

    def _score_text(self, query: str, text: str) -> Decimal:
        normalized_query = query.strip().lower()
        normalized_text = text.lower()
        if not normalized_query:
            return Decimal("0.0000")
        if normalized_query in normalized_text:
            return Decimal("1.0000")
        return Decimal("0.5000")

    def _normalize_target_types(self, target_types: Iterable[str] | None) -> list[str]:
        supported = ["chunk", "file", "knowledge_unit", "wiki_page"]
        if not target_types:
            return ["chunk"]
        normalized = []
        for target_type in target_types:
            if target_type in supported and target_type not in normalized:
                normalized.append(target_type)
        return normalized or ["chunk"]
