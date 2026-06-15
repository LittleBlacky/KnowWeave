from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.base import utcnow
from app.models.chat import ChatMessage, Citation
from app.models.files import Chunk, KnowledgeFile, SourceSpan
from app.models.knowledge import KnowledgeUnit, KnowledgeUnitSource
from app.models.wiki import WikiPage, WikiRevision
from app.providers.factory import build_default_llm_provider
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
    def __init__(self, *, session: Session, llm_provider=None) -> None:
        self.session = session
        self.llm = llm_provider or build_default_llm_provider(get_settings())

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

        self.create_revision(
            wiki_id=wiki.id,
            change_summary="Initial AI-generated draft",
            edit_source="ai_generated",
        )

        for index, chunk in enumerate(chunks, start=1):
            self.session.add(self._citation_for_chunk(wiki, chunk, index=index))

        self.session.commit()
        self.session.refresh(wiki)
        return wiki

    def generate_topic_wiki(
        self,
        *,
        theme: str,
        file_ids: list[UUID] | None = None,
        knowledge_unit_ids: list[UUID] | None = None,
    ) -> WikiPage:
        """Generate a Topic Wiki aggregating evidence across files and KUs."""
        chunks: list[Chunk] = []
        source_files: set[str] = set()

        if file_ids:
            for fid in file_ids:
                file_record = self.session.get(KnowledgeFile, fid)
                if file_record is not None and file_record.deleted_at is None:
                    source_files.add(file_record.name)
                    chunks.extend(self._chunks_for_file(fid))

        if knowledge_unit_ids:
            for kid in knowledge_unit_ids:
                ku = self.session.get(KnowledgeUnit, kid)
                if ku is not None:
                    source_files.add(ku.title)
                    # Find chunks linked to this KU
                    ku_chunks = (
                        self.session.scalars(
                            select(Chunk)
                            .join(KnowledgeUnitSource, KnowledgeUnitSource.chunk_id == Chunk.id)
                            .where(KnowledgeUnitSource.knowledge_unit_id == kid)
                            .where(Chunk.status != "ignored")
                            .limit(5)
                        ).all()
                    )
                    chunks.extend(ku_chunks)

        if not chunks:
            raise WikiChunkRequiredError()

        deduped = {c.id: c for c in chunks}.values()
        content = self._draft_topic_content(theme=theme, chunks=list(deduped), sources=sorted(source_files))

        wiki = WikiPage(
            title=theme,
            wiki_type="topic_wiki",
            status="draft",
            summary=f"Topic wiki across {len(source_files)} sources, {len(deduped)} chunks.",
            content_markdown=content,
            source_file_id=None,
            generation_prompt_version="fake_topic_v1",
            search_text=content,
            metadata_={"source_files": sorted(source_files), "chunk_count": len(deduped)},
            verified_at=None,
        )
        self.session.add(wiki)
        self.session.flush()

        for index, chunk in enumerate(list(deduped), start=1):
            self.session.add(self._citation_for_chunk(wiki, chunk, index=index))

        self.create_revision(wiki_id=wiki.id, change_summary="Initial AI-generated topic wiki", edit_source="ai_generated")
        self.session.commit()
        self.session.refresh(wiki)
        return wiki

    def generate_faq_wiki(self, file_id: UUID) -> WikiPage:
        """Generate a FAQ Wiki from file chunks and recent chat history."""
        file_record = self.session.get(KnowledgeFile, file_id)
        if file_record is None or file_record.deleted_at is not None:
            raise FileNotFoundError()

        chunks = self._chunks_for_file(file_id)
        if not chunks:
            raise WikiChunkRequiredError()

        # Also pull recent chat messages for FAQ context
        recent_messages = self.session.scalars(
            select(ChatMessage)
            .where(ChatMessage.role == "user")
            .order_by(ChatMessage.created_at.desc())
            .limit(10)
        ).all()

        content = self._draft_faq_content(
            file_name=file_record.name,
            chunks=chunks,
            questions=[m.content_markdown for m in recent_messages],
        )

        wiki = WikiPage(
            title=f"{file_record.name} FAQ",
            wiki_type="faq_wiki",
            status="draft",
            summary=f"FAQ wiki generated from {len(chunks)} chunks and {len(recent_messages)} chat questions.",
            content_markdown=content,
            source_file_id=file_record.id,
            generation_prompt_version="fake_faq_v1",
            search_text=content,
            metadata_={"chunk_count": len(chunks), "chat_questions_used": len(recent_messages)},
            verified_at=None,
        )
        self.session.add(wiki)
        self.session.flush()

        for index, chunk in enumerate(chunks, start=1):
            self.session.add(self._citation_for_chunk(wiki, chunk, index=index))

        self.create_revision(wiki_id=wiki.id, change_summary="Initial AI-generated FAQ wiki", edit_source="ai_generated")
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

        self.create_revision(
            wiki_id=wiki.id,
            change_summary=change_summary.strip(),
            edit_source="manual",
        )
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

    # ---- Wiki Revisions ----

    def list_revisions(self, wiki_id: UUID) -> list[WikiRevision]:
        self.get_wiki(wiki_id)
        statement = (
            select(WikiRevision)
            .where(WikiRevision.wiki_page_id == wiki_id)
            .order_by(WikiRevision.revision_number.desc())
        )
        return list(self.session.scalars(statement).all())

    def create_revision(
        self,
        wiki_id: UUID,
        *,
        change_summary: str,
        edit_source: str = "manual",
    ) -> WikiRevision:
        wiki = self.get_wiki(wiki_id)
        existing = self.list_revisions(wiki_id)
        next_number = max((r.revision_number for r in existing), default=0) + 1

        revision = WikiRevision(
            wiki_page_id=wiki.id,
            revision_number=next_number,
            title=wiki.title,
            content_markdown=wiki.content_markdown,
            summary=wiki.summary,
            status=wiki.status,
            change_summary=change_summary,
            edit_source=edit_source,
            created_at=utcnow(),
        )
        self.session.add(revision)
        self.session.commit()
        self.session.refresh(revision)
        return revision

    def rollback_to_revision(self, wiki_id: UUID, revision_id: UUID) -> WikiPage:
        wiki = self.get_wiki(wiki_id)
        revision = self.session.get(WikiRevision, revision_id)
        if revision is None or revision.wiki_page_id != wiki.id:
            raise WikiNotFoundError()

        wiki.title = revision.title
        wiki.content_markdown = revision.content_markdown
        wiki.summary = revision.summary
        wiki.status = revision.status
        wiki.search_text = revision.content_markdown
        wiki.metadata_ = {
            **wiki.metadata_,
            "rolled_back_from_revision": revision.revision_number,
        }
        self.session.add(wiki)
        self.session.commit()
        self.session.refresh(wiki)

        self.create_revision(
            wiki_id=wiki.id,
            change_summary=f"Rolled back to revision {revision.revision_number}",
            edit_source="rollback",
        )
        return wiki

    # ---- Private helpers ----

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

    def _draft_topic_content(self, *, theme: str, chunks: list[Chunk], sources: list[str]) -> str:
        sections = [f"# {theme}", "", f"## Sources: {', '.join(sources)}", "", "## Key Points"]
        for index, chunk in enumerate(chunks, start=1):
            sections.append(f"- {chunk.edited_content or chunk.raw_content} [S{index}]")
        return "\n".join(sections)

    def _draft_faq_content(
        self, *, file_name: str, chunks: list[Chunk], questions: list[str]
    ) -> str:
        sections = [f"# {file_name} FAQ", "", "## Common Questions"]
        for question in questions[:10]:
            sections.append(f"### Q: {question}")
            sections.append(f"A: See source chunks below for relevant policy. [S1]")
        sections.append("")
        sections.append("## Reference Chunks")
        for index, chunk in enumerate(chunks, start=1):
            sections.append(f"- {chunk.edited_content or chunk.raw_content} [S{index}]")
        return "\n".join(sections)
