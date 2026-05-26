from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.evaluation import EvaluationSampleRead
from app.schemas.feedback import FeedbackCreate, FeedbackList, FeedbackRead
from app.services.evaluation_service import EvaluationService
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["feedback"])


def get_feedback_service(db: Session = Depends(get_db)) -> FeedbackService:
    return FeedbackService(session=db)


def get_evaluation_service(db: Session = Depends(get_db)) -> EvaluationService:
    return EvaluationService(session=db)


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


@router.get("")
def list_feedback(
    target_type: str | None = None,
    service: FeedbackService = Depends(get_feedback_service),
) -> ApiResponse[FeedbackList]:
    records = service.list_feedback(target_type=target_type)
    return ApiResponse(
        data=FeedbackList(items=[FeedbackRead.model_validate(record) for record in records], total=len(records)),
        error=None,
        request_id="req_feedback_list",
    )


@router.post("/{feedback_id}/to-evaluation-sample", status_code=status.HTTP_201_CREATED)
def feedback_to_evaluation_sample(
    feedback_id: UUID,
    service: EvaluationService = Depends(get_evaluation_service),
) -> ApiResponse[EvaluationSampleRead]:
    sample = service.create_candidate_from_feedback(feedback_id)
    return ApiResponse(
        data=EvaluationSampleRead.model_validate(sample),
        error=None,
        request_id="req_feedback_to_evaluation",
    )
