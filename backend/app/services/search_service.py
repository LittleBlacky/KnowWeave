from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.base import utcnow
from app.models.chat import RetrievedContext
from app.models.files import Chunk, KnowledgeFile, SourceSpan
from app.services.index_service import IndexService


@dataclass(frozen=True)
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

    def search(self, *, query: str, top_k: int = 10) -> SearchResponse:
        retrieval_run_id = uuid4()
        chunks = self.index.search_chunks(query=query, top_k=top_k)
        results = [
            self._chunk_result(
                chunk,
                rank=index + 1,
                query=query,
                retrieval_run_id=retrieval_run_id,
                top_k=top_k,
            )
            for index, chunk in enumerate(chunks)
        ]
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
            if context.result_type != "chunk":
                continue
            chunk = self.session.get(Chunk, context.result_id)
            if chunk is None:
                continue
            results.append(self._chunk_result_from_context(chunk, context))

        return SearchResponse(
            retrieval_run_id=retrieval_run_id,
            query=contexts[0].query_text,
            strategy=contexts[0].retrieval_strategy,
            results=results,
        )

    def _chunk_result(
        self,
        chunk: Chunk,
        *,
        rank: int,
        query: str,
        retrieval_run_id: UUID,
        top_k: int,
    ) -> SearchResultItem:
        score = self._score_chunk(chunk, query)
        self.session.add(
            RetrievedContext(
                retrieval_run_id=retrieval_run_id,
                chat_message_id=None,
                query_text=query,
                result_type="chunk",
                result_id=chunk.id,
                rank=rank,
                score=score,
                retrieval_strategy="keyword",
                retrieval_params={"top_k": top_k, "target_types": ["chunk"]},
                used_in_answer=False,
                created_at=utcnow(),
            )
        )
        return self._chunk_result_item(chunk, rank=rank, score=score)

    def _chunk_result_from_context(
        self,
        chunk: Chunk,
        context: RetrievedContext,
    ) -> SearchResultItem:
        return self._chunk_result_item(
            chunk,
            rank=context.rank,
            score=context.score or Decimal("0.0000"),
        )

    def _chunk_result_item(self, chunk: Chunk, *, rank: int, score: Decimal) -> SearchResultItem:
        file_record = self.session.get(KnowledgeFile, chunk.file_id)
        source_span = self._source_span_for_chunk(chunk.id)
        preview_text = chunk.edited_content or chunk.raw_content
        return SearchResultItem(
            result_id=chunk.id,
            result_type="chunk",
            title=file_record.name if file_record is not None else "Chunk",
            preview_text=preview_text,
            score=score,
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

    def _source_span_for_chunk(self, chunk_id: UUID) -> SourceSpan | None:
        statement = select(SourceSpan).where(SourceSpan.chunk_id == chunk_id).limit(1)
        return self.session.scalar(statement)

    def _score_chunk(self, chunk: Chunk, query: str) -> Decimal:
        normalized_query = query.strip().lower()
        normalized_text = chunk.search_text.lower()
        if not normalized_query:
            return Decimal("0.0000")
        if normalized_query in normalized_text:
            return Decimal("1.0000")
        return Decimal("0.5000")
