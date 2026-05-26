from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.search import SearchRequest, SearchResponseRead
from app.services.search_service import SearchResponse, SearchService

router = APIRouter(prefix="/search", tags=["search"])


def get_search_service(db: Session = Depends(get_db)) -> SearchService:
    return SearchService(session=db)


@router.post("")
def search(
    request: SearchRequest,
    service: SearchService = Depends(get_search_service),
) -> ApiResponse[SearchResponseRead]:
    result = service.search(query=request.query, top_k=request.top_k)
    return ApiResponse(
        data=_search_response_read(result),
        error=None,
        request_id="req_search",
    )


@router.get("/runs/{retrieval_run_id}")
def get_search_run(
    retrieval_run_id: UUID,
    service: SearchService = Depends(get_search_service),
) -> ApiResponse[SearchResponseRead]:
    result = service.get_retrieval_run(retrieval_run_id)
    return ApiResponse(
        data=_search_response_read(result),
        error=None,
        request_id="req_search_run",
    )


def _search_response_read(result: SearchResponse) -> SearchResponseRead:
    return SearchResponseRead(
        retrieval_run_id=result.retrieval_run_id,
        query=result.query,
        strategy=result.strategy,
        results=[
            {
                "result_id": item.result_id,
                "result_type": item.result_type,
                "title": item.title,
                "preview_text": item.preview_text,
                "score": item.score,
                "rank": item.rank,
                "source": item.source,
                "status": item.status,
                "metadata": item.metadata,
            }
            for item in result.results
        ],
    )
