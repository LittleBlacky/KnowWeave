"""Expert Agent API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agent", tags=["agent"])


def get_agent_service(db: Session = Depends(get_db)) -> AgentService:
    return AgentService(session=db)


@router.post("/generate", status_code=status.HTTP_201_CREATED)
def generate_agent(
    name: str = "知识库专家",
    file_ids: list[UUID] | None = None,
    service: AgentService = Depends(get_agent_service),
) -> ApiResponse[dict]:
    result = service.generate_expert_agent(name=name, file_ids=file_ids)
    return ApiResponse(data=result, error=None, request_id="req_agent_generate")
