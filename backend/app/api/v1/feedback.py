from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.feedback import FeedbackCreate, FeedbackRead
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["feedback"])


def get_feedback_service(db: Session = Depends(get_db)) -> FeedbackService:
    return FeedbackService(session=db)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_feedback(
    request: FeedbackCreate,
    service: FeedbackService = Depends(get_feedback_service),
) -> ApiResponse[FeedbackRead]:
    feedback = service.create_feedback(
        target_type=request.target_type,
        target_id=request.target_id,
        feedback_type=request.feedback_type,
        comment=request.comment,
        metadata=request.metadata,
    )
    return ApiResponse(
        data=FeedbackRead.model_validate(feedback),
        error=None,
        request_id="req_feedback_create",
    )
