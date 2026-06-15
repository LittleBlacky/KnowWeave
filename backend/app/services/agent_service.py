"""Expert Agent generation service.

Creates a specialized Chat session pre-loaded with knowledge base context
so the agent can answer questions based on the uploaded evidence.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.base import utcnow
from app.models.chat import ChatMessage, ChatSession
from app.models.files import Chunk, KnowledgeFile
from app.models.knowledge import KnowledgeUnit
from app.models.wiki import WikiPage


class AgentService:
    def __init__(self, *, session: Session) -> None:
        self.session = session

    def generate_expert_agent(self, *, name: str, file_ids: list[UUID] | None = None) -> dict:
        """Create an expert agent session pre-loaded with knowledge context."""
        # Gather knowledge base summary
        chunks = self._get_chunks(file_ids)
        kus = self._get_knowledge_units(file_ids)
        wikis = self._get_wikis(file_ids)
        files = self._get_files(file_ids)

        # Build system context
        context_parts = [f"你是 {name} 专家，基于以下知识库内容回答问题。"]
        if files:
            context_parts.append(f"\n## 知识文件 ({len(files)} 个)")
            for f in files:
                context_parts.append(f"- {f.name} ({f.file_type})")
        if chunks:
            context_parts.append(f"\n## 知识分块 ({len(chunks)} 个)")
            for c in chunks[:20]:
                context_parts.append(f"- {c.search_text[:200]}")
        if wikis:
            context_parts.append(f"\n## Wiki 页面 ({len(wikis)} 个)")
            for w in wikis:
                context_parts.append(f"- {w.title}: {w.summary or ''}")
        if kus:
            context_parts.append(f"\n## 知识单元 ({len(kus)} 个, 已确认)")
            for ku in kus[:10]:
                context_parts.append(f"- {ku.title}")

        system_prompt = "\n".join(context_parts)

        # Create chat session
        session = ChatSession(title=f"专家: {name}", scope={"agent_type": "expert", "name": name})
        self.session.add(session)
        self.session.flush()

        # Add system message
        msg = ChatMessage(
            session_id=session.id,
            role="system",
            content_markdown=system_prompt,
            status="completed",
            model_provider="system",
            model_name="agent-generator",
            prompt_version="v1",
            created_at=utcnow(),
        )
        self.session.add(msg)
        self.session.commit()

        return {
            "session_id": str(session.id),
            "title": session.title,
            "knowledge_summary": {
                "files": len(files),
                "chunks": len(chunks),
                "knowledge_units": len(kus),
                "wiki_pages": len(wikis),
            },
            "system_prompt_preview": system_prompt[:500],
        }

    def _get_chunks(self, file_ids: list[UUID] | None) -> list[Chunk]:
        stmt = select(Chunk).where(Chunk.is_searchable.is_(True))
        if file_ids:
            stmt = stmt.where(Chunk.file_id.in_(file_ids))
        return list(self.session.scalars(stmt.limit(30)).all())

    def _get_knowledge_units(self, file_ids: list[UUID] | None) -> list[KnowledgeUnit]:
        stmt = select(KnowledgeUnit).where(KnowledgeUnit.status == "verified")
        return list(self.session.scalars(stmt.limit(20)).all())

    def _get_wikis(self, file_ids: list[UUID] | None) -> list[WikiPage]:
        return list(self.session.scalars(select(WikiPage).limit(10)).all())

    def _get_files(self, file_ids: list[UUID] | None) -> list[KnowledgeFile]:
        stmt = select(KnowledgeFile).where(KnowledgeFile.deleted_at.is_(None))
        if file_ids:
            stmt = stmt.where(KnowledgeFile.id.in_(file_ids))
        return list(self.session.scalars(stmt).all())
