"""Curation API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.services.curation_service import CurationService

router = APIRouter(prefix="/curation", tags=["curation"])


def get_curation_service(db: Session = Depends(get_db)) -> CurationService:
    return CurationService(session=db)


@router.get("/report")
def get_curation_report(
    service: CurationService = Depends(get_curation_service),
) -> ApiResponse[dict]:
    report = service.generate_report()
    return ApiResponse(
        data={
            "generated_at": report.generated_at.isoformat(),
            "total_chunks": report.total_chunks,
            "total_knowledge_units": report.total_knowledge_units,
            "total_wiki_pages": report.total_wiki_pages,
            "total_feedback_count": report.total_feedback_count,
            "high_value_chunks": report.high_value_chunks,
            "suggested_topics": report.suggested_topics,
            "frequent_questions": report.frequent_questions,
            "stale_items": report.stale_items,
            "summary": report.summary,
        },
        error=None,
        request_id="req_curation_report",
    )
