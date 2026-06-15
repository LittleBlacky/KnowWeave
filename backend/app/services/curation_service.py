"""LLM-powered knowledge curation service.

Scans the knowledge base and proactively discovers:
- High-value chunks worth promoting to Knowledge Units
- Cross-file themes suitable for Topic Wikis
- Frequent questions from Chat history for FAQ Wiki candidates
- Stale or outdated knowledge needing review
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.base import utcnow
from app.models.chat import ChatMessage, Citation
from app.models.files import Chunk, KnowledgeFile
from app.models.knowledge import KnowledgeUnit
from app.models.wiki import WikiPage
from app.providers.fake_llm import FakeLLMProvider


@dataclass
class CurationReport:
    generated_at: datetime
    total_chunks: int
    total_knowledge_units: int
    total_wiki_pages: int
    total_feedback_count: int
    high_value_chunks: list[dict[str, object]] = field(default_factory=list)
    suggested_topics: list[str] = field(default_factory=list)
    frequent_questions: list[str] = field(default_factory=list)
    stale_items: list[dict[str, object]] = field(default_factory=list)
    summary: str = ""


class CurationService:
    """Scans the knowledge base and produces curation insights.

    Uses simple heuristics + Fake LLM for P1. Real LLM-powered analysis
    can be wired in later via the provider pattern.
    """

    def __init__(self, *, session: Session) -> None:
        self.session = session
        self.llm = FakeLLMProvider()

    def generate_report(self) -> CurationReport:
        now = utcnow()

        # Gather stats
        total_chunks = self.session.scalar(select(func.count()).select_from(Chunk)) or 0
        total_kus = self.session.scalar(select(func.count()).select_from(KnowledgeUnit)) or 0
        total_wikis = self.session.scalar(select(func.count()).select_from(WikiPage)) or 0

        # Count feedback (from citations with source_available=False as proxy)
        feedback_count = self.session.scalar(
            select(func.count()).select_from(Citation).where(Citation.source_available.is_(False))
        ) or 0

        # High-value chunks: edited/verified + referenced in citations
        high_value = self._find_high_value_chunks()

        # Suggested topics from verified KUs
        topics = self._suggest_topics()

        # Frequent questions from chat
        questions = self._frequent_questions()

        # Stale items
        stale = self._find_stale_items(now)

        # Generate summary with Fake LLM
        summary = self._generate_summary(
            total_chunks=total_chunks,
            total_kus=total_kus,
            total_wikis=total_wikis,
            high_value_count=len(high_value),
            topic_count=len(topics),
            question_count=len(questions),
            stale_count=len(stale),
        )

        return CurationReport(
            generated_at=now,
            total_chunks=total_chunks,
            total_knowledge_units=total_kus,
            total_wiki_pages=total_wikis,
            total_feedback_count=feedback_count,
            high_value_chunks=high_value,
            suggested_topics=topics,
            frequent_questions=questions,
            stale_items=stale,
            summary=summary,
        )

    def _find_high_value_chunks(self) -> list[dict[str, object]]:
        """Find chunks cited by wiki pages or with verified KU links."""
        # Chunks that are referenced in citations (wiki citations)
        cited_ids = set(
            self.session.scalars(
                select(Citation.chunk_id).where(Citation.chunk_id.isnot(None))
            ).all()
        )
        verified_chunks = self.session.scalars(
            select(Chunk)
            .where(Chunk.status == "verified")
            .where(Chunk.id.in_(cited_ids) if cited_ids else False)
            .order_by(Chunk.updated_at.desc())
            .limit(10)
        ).all()

        results: list[dict[str, object]] = []
        for chunk in verified_chunks:
            file_record = self.session.get(KnowledgeFile, chunk.file_id)
            results.append({
                "chunk_id": str(chunk.id),
                "file_name": file_record.name if file_record else "unknown",
                "preview": (chunk.edited_content or chunk.raw_content)[:120],
                "status": chunk.status,
                "char_count": chunk.char_count,
            })
        return results

    def _suggest_topics(self) -> list[str]:
        """Suggest topic wiki themes from verified Knowledge Unit titles."""
        verified_kus = self.session.scalars(
            select(KnowledgeUnit.title)
            .where(KnowledgeUnit.status == "verified")
            .limit(20)
        ).all()
        # Simple heuristic: group by first meaningful word
        return list(dict.fromkeys(verified_kus))[:5]

    def _frequent_questions(self) -> list[str]:
        """Extract recent user questions from chat history."""
        messages = self.session.scalars(
            select(ChatMessage.content_markdown)
            .where(ChatMessage.role == "user")
            .order_by(ChatMessage.created_at.desc())
            .limit(20)
        ).all()
        return list(dict.fromkeys(messages))[:10]

    def _find_stale_items(self, now: datetime) -> list[dict[str, object]]:
        """Find chunks/KUs not updated in 30+ days."""
        cutoff = now - timedelta(days=30)
        stale_chunks = self.session.scalars(
            select(Chunk)
            .where(Chunk.status.in_(["draft", "needs_review"]))
            .where(Chunk.updated_at < cutoff)
            .limit(10)
        ).all()
        results: list[dict[str, object]] = []
        for chunk in stale_chunks:
            results.append({
                "id": str(chunk.id),
                "type": "chunk",
                "preview": (chunk.edited_content or chunk.raw_content)[:80],
                "last_updated": chunk.updated_at.isoformat() if chunk.updated_at else "",
            })
        return results

    def _generate_summary(
        self,
        total_chunks: int,
        total_kus: int,
        total_wikis: int,
        high_value_count: int,
        topic_count: int,
        question_count: int,
        stale_count: int,
    ) -> str:
        prompt = (
            f"Knowledge Base Health Report:\n"
            f"- {total_chunks} chunks, {total_kus} knowledge units, {total_wikis} wiki pages\n"
            f"- {high_value_count} high-value chunks identified\n"
            f"- {topic_count} topic wiki suggestions\n"
            f"- {question_count} frequent questions from chat\n"
            f"- {stale_count} stale items need review\n"
            f"Provide a concise summary of knowledge base health and prioritized actions."
        )
        try:
            result = self.llm.generate(prompt)
            return result.content_markdown
        except Exception:
            return f"Knowledge base has {total_chunks} chunks and {total_wikis} wikis. "
            f"{stale_count} items may need review. "
            f"Suggested actions: review stale items, promote {topic_count} topics to wiki."
