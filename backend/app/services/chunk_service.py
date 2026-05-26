from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.base import utcnow
from app.models.files import Chunk, DocumentBlock, KnowledgeFile, ParseResult, SourceSpan
from app.services.chunk_strategy import BlockForChunking, ChunkStrategyOptions, build_chunk_candidates
from app.services.file_service import FileNotFoundError as KnowledgeFileNotFoundError


class ChunkingRequiresParseError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="CHUNKING_REQUIRES_PARSE",
            message="File must be parsed before chunks can be built.",
            status_code=400,
        )


class ChunkService:
    def __init__(self, *, session: Session) -> None:
        self.session = session

    def build_chunks_for_file(
        self,
        file_id: UUID,
        *,
        options: ChunkStrategyOptions | None = None,
    ) -> list[Chunk]:
        file_record = self.session.get(KnowledgeFile, file_id)
        if file_record is None or file_record.deleted_at is not None:
            raise KnowledgeFileNotFoundError()

        parse_result = self._latest_successful_parse_result(file_id)
        if parse_result is None:
            raise ChunkingRequiresParseError()

        blocks = self._blocks_for_parse_result(parse_result.id)
        if not blocks:
            raise ChunkingRequiresParseError()

        self._delete_existing_chunks(file_id)
        candidates = build_chunk_candidates([_block_for_chunking(block) for block in blocks], options=options)
        chunks: list[Chunk] = []
        for index, candidate in enumerate(candidates):
            chunk = Chunk(
                file_id=file_id,
                parse_result_id=parse_result.id,
                document_block_id=candidate.source.block_id,
                parent_chunk_id=None,
                chunk_index=index,
                chunk_type=candidate.chunk_type,
                raw_content=candidate.raw_content,
                edited_content=None,
                is_manually_edited=False,
                summary=None,
                status="draft",
                quality_signals=candidate.quality_signals,
                token_count=None,
                char_count=len(candidate.raw_content),
                search_text=candidate.raw_content,
                metadata_={"strategy": (options or ChunkStrategyOptions()).strategy},
                is_searchable=True,
            )
            self.session.add(chunk)
            self.session.flush()
            self.session.add(
                SourceSpan(
                    file_id=file_id,
                    chunk_id=chunk.id,
                    document_block_id=candidate.source.block_id,
                    page_number=candidate.source.page_number,
                    char_start=candidate.source.char_start,
                    char_end=candidate.source.char_end,
                    line_start=candidate.source.line_start,
                    line_end=candidate.source.line_end,
                    column_start=None,
                    column_end=None,
                    bbox=None,
                    selector=None,
                    preview_text=candidate.source.preview_text,
                    created_at=utcnow(),
                )
            )
            chunks.append(chunk)

        self.session.commit()
        for chunk in chunks:
            self.session.refresh(chunk)
        return chunks

    def list_file_chunks(self, file_id: UUID) -> list[Chunk]:
        file_record = self.session.get(KnowledgeFile, file_id)
        if file_record is None or file_record.deleted_at is not None:
            raise KnowledgeFileNotFoundError()
        statement = select(Chunk).where(Chunk.file_id == file_id).order_by(Chunk.chunk_index.asc())
        return list(self.session.scalars(statement).all())

    def source_spans_for_chunk(self, chunk_id: UUID) -> list[SourceSpan]:
        statement = (
            select(SourceSpan).where(SourceSpan.chunk_id == chunk_id).order_by(SourceSpan.created_at.asc())
        )
        return list(self.session.scalars(statement).all())

    def _latest_successful_parse_result(self, file_id: UUID) -> ParseResult | None:
        statement = (
            select(ParseResult)
            .where(ParseResult.file_id == file_id)
            .where(ParseResult.status == "parse_succeeded")
            .order_by(ParseResult.created_at.desc())
            .limit(1)
        )
        return self.session.scalar(statement)

    def _blocks_for_parse_result(self, parse_result_id: UUID) -> list[DocumentBlock]:
        statement = (
            select(DocumentBlock)
            .where(DocumentBlock.parse_result_id == parse_result_id)
            .where(DocumentBlock.is_ignored.is_(False))
            .order_by(DocumentBlock.block_index.asc())
        )
        return list(self.session.scalars(statement).all())

    def _delete_existing_chunks(self, file_id: UUID) -> None:
        self.session.execute(delete(SourceSpan).where(SourceSpan.file_id == file_id))
        self.session.execute(delete(Chunk).where(Chunk.file_id == file_id))
        self.session.flush()


def _block_for_chunking(block: DocumentBlock) -> BlockForChunking:
    position = block.metadata_.get("position", {})
    return BlockForChunking(
        block_id=block.id,
        block_type=block.block_type,
        raw_content=block.raw_content,
        line_start=position.get("line_start"),
        line_end=position.get("line_end"),
        page_number=block.page_number,
        char_start=block.char_start,
        char_end=block.char_end,
    )
