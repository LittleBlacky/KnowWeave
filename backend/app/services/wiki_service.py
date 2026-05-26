from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.base import utcnow
from app.models.chat import Citation
from app.models.files import Chunk, KnowledgeFile, SourceSpan
from app.models.wiki import WikiPage
from app.services.file_service import FileNotFoundError


class WikiNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(code="WIKI_NOT_FOUND", message="Wiki page not found.", status_code=404)


class WikiChunkRequiredError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="WIKI_CHUNK_REQUIRED",
            message="File must have chunks before a document wiki can be generated.",
            status_code=400,
        )


class WikiChangeSummaryRequiredError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="WIKI_CHANGE_SUMMARY_REQUIRED",
            message="Wiki edits require a change_summary.",
            status_code=400,
        )


class WikiService:
    def __init__(self, *, session: Session) -> None:
        self.session = session

    def generate_document_wiki(self, file_id: UUID) -> WikiPage:
        file_record = self.session.get(KnowledgeFile, file_id)
        if file_record is None or file_record.deleted_at is not None:
            raise FileNotFoundError()

        chunks = self._chunks_for_file(file_id)
        if not chunks:
            raise WikiChunkRequiredError()

        content_markdown = self._draft_content(file_record, chunks)
        wiki = WikiPage(
            title=file_record.name,
            wiki_type="document_wiki",
            status="draft",
            summary=f"Draft wiki generated from {len(chunks)} chunks.",
            content_markdown=content_markdown,
            source_file_id=file_record.id,
            generation_prompt_version="fake_wiki_v1",
            search_text=content_markdown,
            metadata_={"source_chunk_count": len(chunks)},
            verified_at=None,
        )
        self.session.add(wiki)
        self.session.flush()

        for index, chunk in enumerate(chunks, start=1):
            self.session.add(self._citation_for_chunk(wiki, chunk, index=index))

        self.session.commit()
        self.session.refresh(wiki)
        return wiki

    def list_wiki_pages(self) -> list[WikiPage]:
        statement = select(WikiPage).order_by(WikiPage.updated_at.desc())
        return list(self.session.scalars(statement).all())

    def get_wiki(self, wiki_id: UUID) -> WikiPage:
        wiki = self.session.get(WikiPage, wiki_id)
        if wiki is None:
            raise WikiNotFoundError()
        return wiki

    def update_wiki(
        self,
        wiki_id: UUID,
        *,
        change_summary: str,
        content_markdown: str | None = None,
        status: str | None = None,
        summary: str | None = None,
        title: str | None = None,
    ) -> WikiPage:
        if not change_summary.strip():
            raise WikiChangeSummaryRequiredError()

        wiki = self.get_wiki(wiki_id)
        if title is not None:
            wiki.title = title
        if content_markdown is not None:
            wiki.content_markdown = content_markdown
            wiki.search_text = content_markdown
        if summary is not None:
            wiki.summary = summary
        if status is not None:
            wiki.status = status
            if status == "verified":
                wiki.verified_at = utcnow()
        wiki.metadata_ = {**wiki.metadata_, "last_change_summary": change_summary.strip()}
        self.session.add(wiki)
        self.session.commit()
        self.session.refresh(wiki)
        return wiki

    def list_wiki_citations(self, wiki_id: UUID) -> list[Citation]:
        self.get_wiki(wiki_id)
        statement = (
            select(Citation)
            .where(Citation.target_type == "wiki_page")
            .where(Citation.target_id == wiki_id)
            .order_by(Citation.created_at.asc())
        )
        return list(self.session.scalars(statement).all())

    def _chunks_for_file(self, file_id: UUID) -> list[Chunk]:
        statement = (
            select(Chunk)
            .where(Chunk.file_id == file_id)
            .where(Chunk.status != "ignored")
            .order_by(Chunk.chunk_index.asc())
        )
        return list(self.session.scalars(statement).all())

    def _citation_for_chunk(self, wiki: WikiPage, chunk: Chunk, *, index: int) -> Citation:
        source_span = self._source_span_for_chunk(chunk.id)
        file_record = self.session.get(KnowledgeFile, chunk.file_id)
        return Citation(
            target_type="wiki_page",
            target_id=wiki.id,
            file_id=chunk.file_id,
            chunk_id=chunk.id,
            knowledge_unit_id=None,
            source_span_id=source_span.id if source_span is not None else None,
            label=f"S{index}",
            preview_text=chunk.edited_content or chunk.raw_content,
            source_available=file_record is not None and file_record.deleted_at is None,
            created_at=utcnow(),
        )

    def _source_span_for_chunk(self, chunk_id: UUID) -> SourceSpan | None:
        statement = select(SourceSpan).where(SourceSpan.chunk_id == chunk_id).limit(1)
        return self.session.scalar(statement)

    def _draft_content(self, file_record: KnowledgeFile, chunks: list[Chunk]) -> str:
        sections = [f"# {file_record.name}", "", "## Source Summary"]
        for index, chunk in enumerate(chunks, start=1):
            sections.append(f"- {chunk.edited_content or chunk.raw_content} [S{index}]")
        return "\n".join(sections)
