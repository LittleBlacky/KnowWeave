from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import CitationList, CitationRead
from app.schemas.common import ApiResponse
from app.schemas.wiki import WikiPageList, WikiPageRead, WikiUpdateRequest
from app.services.wiki_service import WikiService

router = APIRouter(tags=["wiki"])


def get_wiki_service(db: Session = Depends(get_db)) -> WikiService:
    return WikiService(session=db)


@router.post("/files/{file_id}/wiki", status_code=status.HTTP_201_CREATED)
def create_file_wiki(
    file_id: UUID,
    service: WikiService = Depends(get_wiki_service),
) -> ApiResponse[WikiPageRead]:
    wiki = service.generate_document_wiki(file_id)
    return ApiResponse(data=WikiPageRead.model_validate(wiki), error=None, request_id="req_wiki_create")


@router.get("/wiki/pages")
@router.get("/wiki")
def list_wiki_pages(service: WikiService = Depends(get_wiki_service)) -> ApiResponse[WikiPageList]:
    pages = service.list_wiki_pages()
    return ApiResponse(
        data=WikiPageList(items=[WikiPageRead.model_validate(page) for page in pages], total=len(pages)),
        error=None,
        request_id="req_wiki_list",
    )


@router.get("/wiki/pages/{wiki_id}")
@router.get("/wiki/{wiki_id}")
def get_wiki(
    wiki_id: UUID,
    service: WikiService = Depends(get_wiki_service),
) -> ApiResponse[WikiPageRead]:
    wiki = service.get_wiki(wiki_id)
    return ApiResponse(data=WikiPageRead.model_validate(wiki), error=None, request_id="req_wiki_detail")


@router.patch("/wiki/pages/{wiki_id}")
@router.patch("/wiki/{wiki_id}")
def update_wiki(
    wiki_id: UUID,
    request: WikiUpdateRequest,
    service: WikiService = Depends(get_wiki_service),
) -> ApiResponse[WikiPageRead]:
    wiki = service.update_wiki(
        wiki_id,
        title=request.title,
        content_markdown=request.content_markdown,
        change_summary=request.change_summary,
        status=request.status,
        summary=request.summary,
    )
    return ApiResponse(data=WikiPageRead.model_validate(wiki), error=None, request_id="req_wiki_update")


@router.get("/wiki/pages/{wiki_id}/citations")
@router.get("/wiki/{wiki_id}/citations")
def list_wiki_citations(
    wiki_id: UUID,
    service: WikiService = Depends(get_wiki_service),
) -> ApiResponse[CitationList]:
    citations = service.list_wiki_citations(wiki_id)
    items = [
        CitationRead(
            id=citation.id,
            target_type=citation.target_type,
            target_id=citation.target_id,
            file_id=citation.file_id,
            chunk_id=citation.chunk_id,
            source_span_id=citation.source_span_id,
            label=citation.label,
            preview_text=citation.preview_text,
            source_available=citation.source_available,
        )
        for citation in citations
    ]
    return ApiResponse(
        data=CitationList(items=items, total=len(items)),
        error=None,
        request_id="req_wiki_citations",
    )
