from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.knowledge_units import (
    KnowledgeUnitDetail,
    KnowledgeUnitList,
    KnowledgeUnitMergeRequest,
    KnowledgeUnitRead,
    KnowledgeUnitSourceRead,
    KnowledgeUnitSplitRequest,
    KnowledgeUnitWriteRequest,
)
from app.schemas.tags import TagRead
from app.services.knowledge_unit_service import KnowledgeUnitService

router = APIRouter(prefix="/knowledge-units", tags=["knowledge-units"])


def get_knowledge_unit_service(db: Session = Depends(get_db)) -> KnowledgeUnitService:
    return KnowledgeUnitService(session=db)


@router.get("")
def list_knowledge_units(
    status: str | None = None,
    tag: str | None = None,
    source_file_id: UUID | None = None,
    unit_type: str | None = None,
    service: KnowledgeUnitService = Depends(get_knowledge_unit_service),
) -> ApiResponse[KnowledgeUnitList]:
    units = service.list_knowledge_units(
        status=status,
        tag=tag,
        source_file_id=source_file_id,
        unit_type=unit_type,
    )
    items = [_read_unit(unit, service=service) for unit in units]
    return ApiResponse(
        data=KnowledgeUnitList(items=items, total=len(items)),
        error=None,
        request_id="req_knowledge_unit_list",
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_knowledge_unit(
    request: KnowledgeUnitWriteRequest,
    service: KnowledgeUnitService = Depends(get_knowledge_unit_service),
) -> ApiResponse[KnowledgeUnitRead]:
    unit = service.create_knowledge_unit(
        title=request.title,
        unit_type=request.unit_type,
        content=request.content,
        summary=request.summary,
        status=request.status,
        applicable_scope=request.applicable_scope,
        source_chunk_ids=request.source_chunk_ids,
        tag_ids=request.tag_ids,
    )
    return ApiResponse(
        data=_read_unit(unit, service=service),
        error=None,
        request_id="req_knowledge_unit_create",
    )


@router.post("/files/{file_id}/generate", status_code=status.HTTP_201_CREATED)
def auto_generate_knowledge_units(
    file_id: UUID,
    service: KnowledgeUnitService = Depends(get_knowledge_unit_service),
) -> ApiResponse[KnowledgeUnitList]:
    units = service.auto_generate_from_chunks(file_id)
    items = [_read_unit(unit, service=service) for unit in units]
    return ApiResponse(
        data=KnowledgeUnitList(items=items, total=len(items)),
        error=None,
        request_id="req_auto_knowledge_units",
    )


@router.get("/{knowledge_unit_id}")
def get_knowledge_unit(
    knowledge_unit_id: UUID,
    include_sources: bool = Query(default=True),
    service: KnowledgeUnitService = Depends(get_knowledge_unit_service),
) -> ApiResponse[KnowledgeUnitDetail]:
    unit = service.get_knowledge_unit(knowledge_unit_id)
    sources = service.list_sources(unit.id) if include_sources else []
    return ApiResponse(
        data=KnowledgeUnitDetail(
            **_read_unit(unit, service=service).model_dump(),
            sources=[KnowledgeUnitSourceRead.model_validate(source) for source in sources],
        ),
        error=None,
        request_id="req_knowledge_unit_detail",
    )


@router.patch("/{knowledge_unit_id}")
def update_knowledge_unit(
    knowledge_unit_id: UUID,
    request: KnowledgeUnitWriteRequest,
    service: KnowledgeUnitService = Depends(get_knowledge_unit_service),
) -> ApiResponse[KnowledgeUnitRead]:
    unit = service.update_knowledge_unit(
        knowledge_unit_id,
        title=request.title,
        unit_type=request.unit_type,
        content=request.content,
        summary=request.summary,
        status=request.status,
        applicable_scope=request.applicable_scope,
        source_chunk_ids=request.source_chunk_ids,
        tag_ids=request.tag_ids,
    )
    return ApiResponse(
        data=_read_unit(unit, service=service),
        error=None,
        request_id="req_knowledge_unit_update",
    )


def _read_unit(unit, *, service: KnowledgeUnitService) -> KnowledgeUnitRead:
    sources = service.list_sources(unit.id)
    tags = service.list_tags(unit.id)
    return KnowledgeUnitRead(
        id=unit.id,
        title=unit.title,
        unit_type=unit.unit_type,
        content=unit.content,
        summary=unit.summary,
        status=unit.status,
        trust_level=unit.trust_level,
        applicable_scope=unit.applicable_scope,
        created_from=unit.created_from,
        search_text=unit.search_text,
        metadata_=unit.metadata_,
        source_count=len(sources),
        tags=[TagRead.model_validate(tag) for tag in tags],
        created_at=unit.created_at,
        updated_at=unit.updated_at,
        verified_at=unit.verified_at,
        archived_at=unit.archived_at,
    )


@router.post("/merge", status_code=status.HTTP_201_CREATED)
def merge_knowledge_units(
    request: KnowledgeUnitMergeRequest,
    service: KnowledgeUnitService = Depends(get_knowledge_unit_service),
) -> ApiResponse[KnowledgeUnitRead]:
    merged = service.merge_knowledge_units(source_ids=request.source_ids, title=request.title)
    return ApiResponse(
        data=_read_unit(merged, service=service),
        error=None,
        request_id="req_ku_merge",
    )


@router.post("/split", status_code=status.HTTP_201_CREATED)
def split_knowledge_unit(
    request: KnowledgeUnitSplitRequest,
    service: KnowledgeUnitService = Depends(get_knowledge_unit_service),
) -> ApiResponse[KnowledgeUnitList]:
    units = service.split_knowledge_unit(
        source_id=request.source_id,
        titles=request.titles,
        content_splits=request.content_splits,
    )
    items = [_read_unit(u, service=service) for u in units]
    return ApiResponse(
        data=KnowledgeUnitList(items=items, total=len(items)),
        error=None,
        request_id="req_ku_split",
    )
