from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.tags import TagBindingRead, TagBindingRequest, TagList, TagRead, TagWriteRequest
from app.services.tag_service import TagService

router = APIRouter(tags=["tags"])


def get_tag_service(db: Session = Depends(get_db)) -> TagService:
    return TagService(session=db)


@router.get("/tags")
def list_tags(service: TagService = Depends(get_tag_service)) -> ApiResponse[TagList]:
    rows = service.list_tags()
    items = [
        TagRead(
            id=row.tag.id,
            name=row.tag.name,
            description=row.tag.description,
            color=row.tag.color,
            binding_count=row.binding_count,
            created_at=row.tag.created_at,
            updated_at=row.tag.updated_at,
        )
        for row in rows
    ]
    return ApiResponse(
        data=TagList(items=items, total=len(items)),
        error=None,
        request_id="req_tag_list",
    )


@router.post("/tags", status_code=status.HTTP_201_CREATED)
def create_tag(
    request: TagWriteRequest,
    service: TagService = Depends(get_tag_service),
) -> ApiResponse[TagRead]:
    tag = service.create_tag(
        name=request.name,
        description=request.description,
        color=request.color,
    )
    return ApiResponse(
        data=TagRead.model_validate(tag),
        error=None,
        request_id="req_tag_create",
    )


@router.patch("/tags/{tag_id}")
def update_tag(
    tag_id: UUID,
    request: TagWriteRequest,
    service: TagService = Depends(get_tag_service),
) -> ApiResponse[TagRead]:
    tag = service.update_tag(
        tag_id,
        name=request.name,
        description=request.description,
        color=request.color,
    )
    return ApiResponse(
        data=TagRead.model_validate(tag),
        error=None,
        request_id="req_tag_update",
    )


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: UUID,
    service: TagService = Depends(get_tag_service),
) -> Response:
    service.delete_tag(tag_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/tag-bindings", status_code=status.HTTP_201_CREATED)
def bind_tag(
    request: TagBindingRequest,
    service: TagService = Depends(get_tag_service),
) -> ApiResponse[TagBindingRead]:
    binding = service.bind_tag(
        tag_id=request.tag_id,
        target_type=request.target_type,
        target_id=request.target_id,
    )
    return ApiResponse(
        data=TagBindingRead.model_validate(binding),
        error=None,
        request_id="req_tag_binding_create",
    )


@router.delete("/tag-bindings", status_code=status.HTTP_204_NO_CONTENT)
def remove_tag_binding(
    request: TagBindingRequest,
    service: TagService = Depends(get_tag_service),
) -> Response:
    service.remove_binding(
        tag_id=request.tag_id,
        target_type=request.target_type,
        target_id=request.target_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
