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

    # ---- Sync wrappers (backward compat) ----

    def generate_document_wiki(self, file_id: UUID) -> WikiPage:
        import asyncio
        return asyncio.run(self.generate_document_wiki_async(file_id))

    def generate_topic_wiki(
        self, *, theme: str, file_ids=None, knowledge_unit_ids=None,
    ) -> WikiPage:
        import asyncio
        return asyncio.run(
            self.generate_topic_wiki_async(
                theme=theme, file_ids=file_ids, knowledge_unit_ids=knowledge_unit_ids,
            )
        )

    def generate_faq_wiki(self, file_id: UUID) -> WikiPage:
        import asyncio
        return asyncio.run(self.generate_faq_wiki_async(file_id))

    # ---- Async generate (call these from async endpoints) ----

    async def generate_document_wiki_async(self, file_id: UUID) -> WikiPage:
        file_record = self.session.get(KnowledgeFile, file_id)
        if file_record is None or file_record.deleted_at is not None:
            raise FileNotFoundError()

        chunks = self._chunks_for_file(file_id)
        if not chunks:
            raise WikiChunkRequiredError()

        content_markdown = await self._draft_content_async(file_record, chunks)
        wiki = WikiPage(
            title=file_record.name,
            wiki_type="document_wiki",
            status="draft",
            summary=f"AI 编译自 {len(chunks)} 个知识片段",
            content_markdown=content_markdown,
            source_file_id=file_record.id,
            generation_prompt_version="llm_wiki_v1",
            search_text=content_markdown,
            metadata_={"source_chunk_count": len(chunks)},
            verified_at=None,
        )
        self.session.add(wiki)
        self.session.flush()
        self._create_revision_and_citations(wiki, chunks)
        self.session.commit()
        self.session.refresh(wiki)
        return wiki

    async def generate_topic_wiki_async(
        self,
        *,
        theme: str,
        file_ids: list[UUID] | None = None,
        knowledge_unit_ids: list[UUID] | None = None,
    ) -> WikiPage:
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

        deduped = list({c.id: c for c in chunks}.values())
        content = await self._draft_topic_content_async(
            theme=theme, chunks=deduped, sources=sorted(source_files)
        )
        wiki = WikiPage(
            title=theme,
            wiki_type="topic_wiki",
            status="draft",
            summary=f"AI 综合 {len(source_files)} 个来源的 {len(deduped)} 个片段",
            content_markdown=content,
            source_file_id=None,
            generation_prompt_version="llm_topic_v1",
            search_text=content,
            metadata_={"source_files": sorted(source_files), "chunk_count": len(deduped)},
            verified_at=None,
        )
        self.session.add(wiki)
        self.session.flush()
        self._create_revision_and_citations(wiki, deduped)
        self.session.commit()
        self.session.refresh(wiki)
        return wiki

    async def generate_faq_wiki_async(self, file_id: UUID) -> WikiPage:
        file_record = self.session.get(KnowledgeFile, file_id)
        if file_record is None or file_record.deleted_at is not None:
            raise FileNotFoundError()

        chunks = self._chunks_for_file(file_id)
        if not chunks:
            raise WikiChunkRequiredError()

        recent_messages = self.session.scalars(
            select(ChatMessage)
            .where(ChatMessage.role == "user")
            .order_by(ChatMessage.created_at.desc())
            .limit(10)
        ).all()

        content = await self._draft_faq_content_async(
            file_name=file_record.name,
            chunks=chunks,
            questions=[m.content_markdown for m in recent_messages],
        )
        wiki = WikiPage(
            title=f"{file_record.name} FAQ",
            wiki_type="faq_wiki",
            status="draft",
            summary=f"AI 基于 {len(chunks)} 个片段和 {len(recent_messages)} 个问题生成的 FAQ",
            content_markdown=content,
            source_file_id=file_record.id,
            generation_prompt_version="llm_faq_v1",
            search_text=content,
            metadata_={"chunk_count": len(chunks), "chat_questions_used": len(recent_messages)},
            verified_at=None,
        )
        self.session.add(wiki)
        self.session.flush()
        self._create_revision_and_citations(wiki, chunks)
        self.session.commit()
        self.session.refresh(wiki)
        return wiki

    def _create_revision_and_citations(self, wiki: WikiPage, chunks: list[Chunk]) -> None:
        self.create_revision(
            wiki_id=wiki.id,
            change_summary="Initial AI-generated draft",
            edit_source="ai_generated",
        )
        for index, chunk in enumerate(chunks, start=1):
            self.session.add(self._citation_for_chunk(wiki, chunk, index=index))

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
        """同步包装：在已有 event loop 中调用异步方法时使用 run_in_executor 策略。
        实际逻辑在 _draft_content_async 中。"""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._draft_content_async(file_record, chunks))
        # 已有运行中的 loop（如 FastAPI 请求上下文中），无法 run_until_complete。
        # 回退到原文本拼接 — 调用者应在 async 上下文中直接使用 _draft_content_async。
        return self._draft_content_sync(file_record, chunks)

    async def _draft_content_async(self, file_record: KnowledgeFile, chunks: list[Chunk]) -> str:
        """LLM 编译 Document Wiki：读取所有 chunk → 生成结构化 Markdown + 引用标记。"""
        context = _chunks_context(chunks)
        prompt = f"""你是知识整理专家。根据以下文档片段，生成一份结构化的 Wiki 页面（Markdown 格式）。

## 要求
1. 先分析文档主题，给出一句概括性导语
2. 按逻辑结构组织章节（如：背景、规则、流程、注意事项等），使用 ## 二级标题
3. 用自己的话重述内容，不要逐字复制原文
4. 每个事实陈述后标注来源编号，如 [S1] [S2]
5. 在文末附加"## 来源索引"，列出每个来源编号对应的原文摘要

## 文档名称
{file_record.name}

## 文档片段
{context}"""

        try:
            result = await self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.3, "max_tokens": 4096},
            )
            return result.content
        except Exception:
            return self._draft_content_sync(file_record, chunks)

    @staticmethod
    def _draft_content_sync(file_record: KnowledgeFile, chunks: list[Chunk]) -> str:
        """回退：原文拼接（LLM 不可用时）。"""
        sections = [f"# {file_record.name}", "", "> *由 AI 编译失败，显示原始片段整合*", "", "## 片段整合"]
        for index, chunk in enumerate(chunks, start=1):
            sections.append(f"{chunk.edited_content or chunk.raw_content} [S{index}]")
        return "\n".join(sections)

    def _draft_topic_content(self, *, theme: str, chunks: list[Chunk], sources: list[str]) -> str:
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._draft_topic_content_async(theme=theme, chunks=chunks, sources=sources))
        return self._draft_topic_sync(theme=theme, chunks=chunks, sources=sources)

    async def _draft_topic_content_async(
        self, *, theme: str, chunks: list[Chunk], sources: list[str]
    ) -> str:
        context = _chunks_context(chunks)
        prompt = f"""你是知识综合专家。根据以下跨文件的知识片段，撰写一份主题 Wiki 页面。

## 主题
{theme}

## 涉及来源
{', '.join(sources)}

## 要求
1. 开头用一段话综述该主题的核心要点
2. 按子主题组织章节（## 标题）
3. 综合多个来源的信息，指出不同来源的一致或补充关系
4. 所有事实标注来源编号 [S1] [S2]
5. 文末列出"## 来源索引"

## 知识片段
{context}"""

        try:
            result = await self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.4, "max_tokens": 4096},
            )
            return result.content
        except Exception:
            return self._draft_topic_sync(theme=theme, chunks=chunks, sources=sources)

    @staticmethod
    def _draft_topic_sync(*, theme: str, chunks: list[Chunk], sources: list[str]) -> str:
        sections = [f"# {theme}", "", f"*来源: {', '.join(sources)}*", "", "## 要点整合"]
        for idx, chunk in enumerate(chunks, start=1):
            sections.append(f"- {chunk.edited_content or chunk.raw_content} [S{idx}]")
        return "\n".join(sections)

    def _draft_faq_content(
        self, *, file_name: str, chunks: list[Chunk], questions: list[str]
    ) -> str:
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(
                self._draft_faq_content_async(file_name=file_name, chunks=chunks, questions=questions)
            )
        return self._draft_faq_sync(file_name=file_name, chunks=chunks, questions=questions)

    async def _draft_faq_content_async(
        self, *, file_name: str, chunks: list[Chunk], questions: list[str]
    ) -> str:
        context = _chunks_context(chunks)
        questions_text = "\n".join(f"- {q}" for q in questions[:10]) if questions else "(无历史提问)"
        prompt = f"""你是 FAQ 编写专家。根据以下文档内容和用户常见问题，生成一份 FAQ Wiki 页面。

## 文档
{file_name}

## 用户常问问题
{questions_text}

## 要求
1. 以问答形式组织（## Q: ... / A: ...）
2. 答案基于文档内容，不要编造
3. 每个答案标注引用 [S1] [S2]
4. 如果文档不能回答某问题，写 "A: 当前文档未涉及此内容"
5. 文末列出"## 来源索引"

## 文档内容
{context}"""

        try:
            result = await self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.3, "max_tokens": 4096},
            )
            return result.content
        except Exception:
            return self._draft_faq_sync(file_name=file_name, chunks=chunks, questions=questions)

    @staticmethod
    def _draft_faq_sync(*, file_name: str, chunks: list[Chunk], questions: list[str]) -> str:
        sections = [f"# {file_name} FAQ", "", "## 常见问题"]
        for question in questions[:10]:
            sections.append(f"### Q: {question}")
            sections.append("A: 参考下方来源片段。")
        sections.append("")
        sections.append("## 来源片段")
        for idx, chunk in enumerate(chunks, start=1):
            sections.append(f"- {chunk.edited_content or chunk.raw_content} [S{idx}]")
        return "\n".join(sections)


def _chunks_context(chunks: list[Chunk]) -> str:
    """Format chunks as a numbered context block for LLM prompts."""
    parts: list[str] = []
    for idx, chunk in enumerate(chunks, start=1):
        text = (chunk.edited_content or chunk.raw_content).strip()
        parts.append(f"[S{idx}] {text}")
    return "\n\n".join(parts)
