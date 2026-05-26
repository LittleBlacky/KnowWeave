from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.files import Chunk
from app.schemas.common import ApiResponse
from app.schemas.files import ChunkRead, ChunkUpdateRequest, SourceSpanRead
from app.services.chunk_service import ChunkService

router = APIRouter(prefix="/chunks", tags=["chunks"])


def get_chunk_service(db: Session = Depends(get_db)) -> ChunkService:
    return ChunkService(session=db)


@router.get("/{chunk_id}")
def get_chunk(
    chunk_id: UUID,
    service: ChunkService = Depends(get_chunk_service),
) -> ApiResponse[ChunkRead]:
    chunk = service.get_chunk(chunk_id)
    return ApiResponse(
        data=_chunk_read(chunk, service=service),
        error=None,
        request_id="req_chunk_detail",
    )


@router.patch("/{chunk_id}")
def update_chunk(
    chunk_id: UUID,
    request: ChunkUpdateRequest,
    service: ChunkService = Depends(get_chunk_service),
) -> ApiResponse[ChunkRead]:
    chunk = service.update_chunk(
        chunk_id,
        edited_content=request.edited_content,
        status=request.status,
        summary=request.summary,
    )
    return ApiResponse(
        data=_chunk_read(chunk, service=service),
        error=None,
        request_id="req_chunk_update",
    )


@router.post("/{chunk_id}/ignore")
def ignore_chunk(
    chunk_id: UUID,
    service: ChunkService = Depends(get_chunk_service),
) -> ApiResponse[ChunkRead]:
    chunk = service.ignore_chunk(chunk_id)
    return ApiResponse(
        data=_chunk_read(chunk, service=service),
        error=None,
        request_id="req_chunk_ignore",
    )


@router.post("/{chunk_id}/verify")
def verify_chunk(
    chunk_id: UUID,
    service: ChunkService = Depends(get_chunk_service),
) -> ApiResponse[ChunkRead]:
    chunk = service.verify_chunk(chunk_id)
    return ApiResponse(
        data=_chunk_read(chunk, service=service),
        error=None,
        request_id="req_chunk_verify",
    )


def _chunk_read(chunk: Chunk, *, service: ChunkService) -> ChunkRead:
    spans = service.source_spans_for_chunk(chunk.id)
    return ChunkRead(
        id=chunk.id,
        file_id=chunk.file_id,
        parse_result_id=chunk.parse_result_id,
        document_block_id=chunk.document_block_id,
        chunk_index=chunk.chunk_index,
        chunk_type=chunk.chunk_type,
        raw_content=chunk.raw_content,
        edited_content=chunk.edited_content,
        is_manually_edited=chunk.is_manually_edited,
        status=chunk.status,
        summary=chunk.summary,
        quality_signals=chunk.quality_signals,
        char_count=chunk.char_count,
        search_text=chunk.search_text,
        is_searchable=chunk.is_searchable,
        source_spans=[
            SourceSpanRead(
                id=span.id,
                document_block_id=span.document_block_id,
                page_number=span.page_number,
                char_start=span.char_start,
                char_end=span.char_end,
                line_start=span.line_start,
                line_end=span.line_end,
                preview_text=span.preview_text,
            )
            for span in spans
        ],
    )
