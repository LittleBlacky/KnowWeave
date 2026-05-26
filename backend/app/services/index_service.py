from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.files import Chunk, KnowledgeFile


class IndexService:
    def __init__(self, *, session: Session) -> None:
        self.session = session

    def search_chunks(self, *, query: str, top_k: int) -> list[Chunk]:
        normalized_query = query.strip().lower()
        if not normalized_query:
            return []

        statement = (
            select(Chunk)
            .join(KnowledgeFile, KnowledgeFile.id == Chunk.file_id)
            .where(KnowledgeFile.deleted_at.is_(None))
            .where(KnowledgeFile.status != "soft_deleted")
            .where(Chunk.is_searchable.is_(True))
            .where(Chunk.status.notin_(["ignored", "archived"]))
            .where(func.lower(Chunk.search_text).contains(normalized_query))
            .order_by(Chunk.chunk_index.asc())
            .limit(top_k)
        )
        return list(self.session.scalars(statement).all())
