from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.files import DocumentBlock
from app.providers.storage import LocalStorageProvider
from app.schemas.common import ApiResponse
from app.schemas.files import (
    DocumentBlockList,
    DocumentBlockRead,
    FileDetail,
    FileList,
    FileRead,
    ParseResultRead,
)
from app.services.file_service import FileService
from app.services.parsing_service import ParsingService

router = APIRouter(prefix="/files", tags=["files"])


def get_file_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> FileService:
    return FileService(
        session=db,
        storage=LocalStorageProvider(settings.file_storage_root),
        max_upload_mb=settings.max_upload_mb,
    )


def get_parsing_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ParsingService:
    return ParsingService(
        session=db,
        storage=LocalStorageProvider(settings.file_storage_root),
    )


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    directory_path: str = Form(default=""),
    service: FileService = Depends(get_file_service),
) -> ApiResponse[FileRead]:
    content = await file.read()
    record = service.create_file(
        filename=file.filename or "uploaded-file",
        content_type=file.content_type or "application/octet-stream",
        content=content,
        directory_path=directory_path,
    )
    return ApiResponse(
        data=FileRead.model_validate(record),
        error=None,
        request_id="req_upload",
    )


@router.get("")
def list_files(service: FileService = Depends(get_file_service)) -> ApiResponse[FileList]:
    records = service.list_files()
    return ApiResponse(
        data=FileList(items=[FileRead.model_validate(record) for record in records], total=len(records)),
        error=None,
        request_id="req_files",
    )


@router.get("/{file_id}")
def get_file(file_id: UUID, service: FileService = Depends(get_file_service)) -> ApiResponse[FileDetail]:
    record = service.get_file(file_id)
    return ApiResponse(
        data=FileDetail.model_validate(record),
        error=None,
        request_id="req_file_detail",
    )


@router.post("/{file_id}/parse")
def parse_file(
    file_id: UUID,
    service: ParsingService = Depends(get_parsing_service),
) -> ApiResponse[ParseResultRead]:
    parse_result = service.parse_file(file_id)
    block_count = service.session.scalar(
        select(func.count()).select_from(DocumentBlock).where(DocumentBlock.parse_result_id == parse_result.id)
    )
    return ApiResponse(
        data=ParseResultRead(
            id=parse_result.id,
            file_id=parse_result.file_id,
            parser_name=parse_result.parser_name,
            parser_version=parse_result.parser_version,
            status=parse_result.status,
            raw_text=parse_result.raw_text,
            warnings=parse_result.warnings,
            error_message=parse_result.error_message,
            parse_metadata=parse_result.parse_metadata,
            block_count=block_count or 0,
            created_at=parse_result.created_at,
        ),
        error=None,
        request_id="req_parse",
    )


@router.get("/{file_id}/blocks")
def list_document_blocks(
    file_id: UUID,
    service: ParsingService = Depends(get_parsing_service),
) -> ApiResponse[DocumentBlockList]:
    blocks = service.list_blocks(file_id)
    items = [_document_block_read(block) for block in blocks]
    return ApiResponse(
        data=DocumentBlockList(items=items, total=len(items)),
        error=None,
        request_id="req_document_blocks",
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: UUID,
    service: FileService = Depends(get_file_service),
) -> Response:
    service.soft_delete_file(file_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _document_block_read(block: DocumentBlock) -> DocumentBlockRead:
    position = block.metadata_.get("position", {})
    metadata = {key: value for key, value in block.metadata_.items() if key != "position"}
    return DocumentBlockRead(
        id=block.id,
        file_id=block.file_id,
        parse_result_id=block.parse_result_id,
        block_index=block.block_index,
        block_type=block.block_type,
        raw_content=block.raw_content,
        normalized_content=block.normalized_content,
        is_ignored=block.is_ignored,
        page_number=block.page_number,
        line_start=position.get("line_start"),
        line_end=position.get("line_end"),
        char_start=block.char_start,
        char_end=block.char_end,
        metadata=metadata,
        created_at=block.created_at,
    )
