from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.evaluation import (
    EvaluationSampleCreate,
    EvaluationSampleList,
    EvaluationSampleRead,
    EvaluationSampleUpdate,
)
from app.services.evaluation_service import EvaluationService

router = APIRouter(tags=["evaluation"])


def get_evaluation_service(db: Session = Depends(get_db)) -> EvaluationService:
    return EvaluationService(session=db)


@router.post("/evaluation-samples", status_code=status.HTTP_201_CREATED)
def create_evaluation_sample(
    request: EvaluationSampleCreate,
    service: EvaluationService = Depends(get_evaluation_service),
) -> ApiResponse[EvaluationSampleRead]:
    sample = service.create_manual_candidate(
        question=request.question,
        expected_answer=request.expected_answer,
        expected_source_files=request.expected_source_files,
        expected_source_chunks=request.expected_source_chunks,
        created_from=request.created_from,
        status=request.status,
        difficulty=request.difficulty,
        metadata=request.metadata,
    )
    return ApiResponse(
        data=EvaluationSampleRead.model_validate(sample),
        error=None,
        request_id="req_evaluation_sample_create",
    )


@router.get("/evaluation-samples")
def list_evaluation_samples(
    status_filter: str | None = Query(default=None, alias="status"),
    service: EvaluationService = Depends(get_evaluation_service),
) -> ApiResponse[EvaluationSampleList]:
    samples = service.list_samples(status=status_filter)
    return ApiResponse(
        data=EvaluationSampleList(
            items=[EvaluationSampleRead.model_validate(sample) for sample in samples],
            total=len(samples),
        ),
        error=None,
        request_id="req_evaluation_sample_list",
    )


@router.get("/evaluation/metrics")
def get_evaluation_metrics(
    service: EvaluationService = Depends(get_evaluation_service),
) -> ApiResponse[dict]:
    metrics = service.run_metrics()
    return ApiResponse(data=metrics, error=None, request_id="req_evaluation_metrics")


@router.get("/evaluation-samples/{sample_id}")
def get_evaluation_sample(
    sample_id: UUID,
    service: EvaluationService = Depends(get_evaluation_service),
) -> ApiResponse[EvaluationSampleRead]:
    sample = service.get_sample(sample_id)
    return ApiResponse(
        data=EvaluationSampleRead.model_validate(sample),
        error=None,
        request_id="req_evaluation_sample_get",
    )


@router.patch("/evaluation-samples/{sample_id}")
def update_evaluation_sample(
    sample_id: UUID,
    request: EvaluationSampleUpdate,
    service: EvaluationService = Depends(get_evaluation_service),
) -> ApiResponse[EvaluationSampleRead]:
    sample = service.update_sample(
        sample_id,
        question=request.question,
        expected_answer=request.expected_answer,
        status=request.status,
        difficulty=request.difficulty,
    )
    return ApiResponse(
        data=EvaluationSampleRead.model_validate(sample),
        error=None,
        request_id="req_evaluation_sample_update",
    )

