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


@router.post("/trigger")
def trigger_curation(
    service: CurationService = Depends(get_curation_service),
) -> ApiResponse[dict]:
    """Manually trigger a curation scan. In production this would be called by a scheduler."""
    report = service.generate_report()
    actions: list[str] = []

    # Auto-create Topic Wiki from top suggestion
    if report.suggested_topics:
        try:
            from app.services.wiki_service import WikiService
            wiki_svc = WikiService(session=service.session)
            # Create Topic Wiki for the first suggested topic if there are verified KUs
            wiki_svc.generate_topic_wiki(
                theme=f"Auto: {report.suggested_topics[0]}",
                file_ids=None,
                knowledge_unit_ids=None,
            )
            actions.append(f"Created Topic Wiki: {report.suggested_topics[0]}")
        except Exception:
            pass

    actions.append(f"Found {len(report.high_value_chunks)} high-value chunks")
    actions.append(f"Found {len(report.stale_items)} stale items to review")
    actions.append(f"Found {len(report.frequent_questions)} frequent questions")

    return ApiResponse(
        data={"triggered": True, "actions": actions},
        error=None,
        request_id="req_curation_trigger",
    )
