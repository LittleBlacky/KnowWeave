from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import (
    ChatMessageRequest,
    ChatSessionCreate,
    ChatSessionRead,
    CitationList,
    CitationRead,
)
from app.schemas.common import ApiResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service(db: Session = Depends(get_db)) -> ChatService:
    return ChatService(session=db)


@router.post("/sessions", status_code=201)
def create_session(
    request: ChatSessionCreate,
    service: ChatService = Depends(get_chat_service),
) -> ApiResponse[ChatSessionRead]:
    session = service.create_session(title=request.title)
    return ApiResponse(
        data=ChatSessionRead(
            id=session.id,
            title=session.title,
            scope=session.scope,
            created_at=session.created_at,
            updated_at=session.updated_at,
        ),
        error=None,
        request_id="req_chat_session_create",
    )


@router.post("/sessions/{session_id}/messages")
def send_message(
    session_id: UUID,
    request: ChatMessageRequest,
    service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    return StreamingResponse(
        service.stream_answer(session_id=session_id, question=request.question, top_k=request.top_k),
        media_type="text/event-stream",
    )


@router.get("/messages/{message_id}/citations")
def list_message_citations(
    message_id: UUID,
    service: ChatService = Depends(get_chat_service),
) -> ApiResponse[CitationList]:
    citations = service.list_citations(message_id)
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
        request_id="req_chat_citations",
    )
