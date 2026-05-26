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

        statement = select(Chunk).join(KnowledgeFile, KnowledgeFile.id == Chunk.file_id).where(
            KnowledgeFile.deleted_at.is_(None),
            KnowledgeFile.status != "soft_deleted",
            Chunk.is_searchable.is_(True),
            Chunk.status.notin_(["ignored", "archived"]),
        )

        if self.session.get_bind().dialect.name == "postgresql":
            vector = func.to_tsvector("simple", Chunk.search_text)
            ts_query = func.plainto_tsquery("simple", query.strip())
            statement = statement.where(vector.op("@@")(ts_query)).order_by(
                func.ts_rank(vector, ts_query).desc(),
                Chunk.chunk_index.asc(),
            )
        else:
            statement = statement.where(func.lower(Chunk.search_text).contains(normalized_query)).order_by(
                Chunk.chunk_index.asc()
            )

        statement = statement.limit(top_k)
        return list(self.session.scalars(statement).all())
