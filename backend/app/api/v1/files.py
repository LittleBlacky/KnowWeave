from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.providers.storage import LocalStorageProvider
from app.schemas.common import ApiResponse
from app.schemas.files import FileDetail, FileList, FileRead
from app.services.file_service import FileService

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


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: UUID,
    service: FileService = Depends(get_file_service),
) -> Response:
    service.soft_delete_file(file_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
