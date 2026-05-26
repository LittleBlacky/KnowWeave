from __future__ import annotations

from collections.abc import AsyncIterator
import json
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.base import utcnow
from app.models.chat import ChatMessage, ChatSession, Citation, RetrievedContext
from app.providers.base import LLMProvider, LLMProviderError
from app.providers.factory import build_default_llm_provider
from app.services.search_service import SearchResultItem, SearchService


class ChatSessionNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(code="CHAT_SESSION_NOT_FOUND", message="Chat session not found.", status_code=404)


class ChatMessageNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(code="CHAT_MESSAGE_NOT_FOUND", message="Chat message not found.", status_code=404)


class ChatService:
    def __init__(
        self,
        *,
        session: Session,
        search_service: SearchService | None = None,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self.session = session
        self.search_service = search_service or SearchService(session=session)
        self.llm_provider = llm_provider or build_default_llm_provider(get_settings())

    def create_session(self, *, title: str) -> ChatSession:
        chat_session = ChatSession(title=title, scope={})
        self.session.add(chat_session)
        self.session.commit()
        self.session.refresh(chat_session)
        return chat_session

    def list_sessions(self) -> list[ChatSession]:
        statement = select(ChatSession).order_by(ChatSession.updated_at.desc())
        return list(self.session.scalars(statement).all())

    def get_session(self, session_id: UUID) -> ChatSession:
        chat_session = self.session.get(ChatSession, session_id)
        if chat_session is None:
            raise ChatSessionNotFoundError()
        return chat_session

    def list_session_messages(self, session_id: UUID) -> list[ChatMessage]:
        self.get_session(session_id)
        statement = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return list(self.session.scalars(statement).all())

    def list_citations(self, message_id: UUID) -> list[Citation]:
        message = self.session.get(ChatMessage, message_id)
        if message is None:
            raise ChatMessageNotFoundError()
        statement = (
            select(Citation)
            .where(Citation.target_type == "chat_message")
            .where(Citation.target_id == message_id)
            .order_by(Citation.created_at.asc())
        )
        return list(self.session.scalars(statement).all())

    async def stream_answer(
        self,
        *,
        session_id: UUID,
        question: str,
        top_k: int,
    ) -> AsyncIterator[str]:
        self.get_session(session_id)
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content_markdown=question,
            status="completed",
            model_provider=None,
            model_name=None,
            prompt_version=None,
            created_at=utcnow(),
        )
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content_markdown="",
            status="streaming",
            model_provider=_provider_name(self.llm_provider),
            model_name=_provider_model_name(self.llm_provider),
            prompt_version="chat_qa_v1",
            created_at=utcnow(),
        )
        self.session.add_all([user_message, assistant_message])
        self.session.commit()
        self.session.refresh(assistant_message)

        search_response = self.search_service.search(query=question, top_k=top_k)
        self._attach_retrieval_contexts(search_response.retrieval_run_id, assistant_message.id)

        yield _sse(
            "start",
            {
                "message_id": str(assistant_message.id),
                "retrieval_run_id": str(search_response.retrieval_run_id),
            },
        )
        yield _sse(
            "retrieval",
            {
                "retrieval_run_id": str(search_response.retrieval_run_id),
                "results": [_search_result_payload(item) for item in search_response.results],
            },
        )

        answer_parts: list[str] = []
        try:
            async for event in self.llm_provider.stream(
                messages=_chat_messages(question=question, results=search_response.results),
                options={},
            ):
                if event.type == "delta" and event.text:
                    answer_parts.append(event.text)
                    yield _sse(
                        "delta",
                        {"message_id": str(assistant_message.id), "delta": event.text},
                    )
        except LLMProviderError as exc:
            assistant_message.status = "failed"
            self.session.add(assistant_message)
            self.session.commit()
            yield _sse(
                "error",
                {
                    "message_id": str(assistant_message.id),
                    "status": "failed",
                    "message": str(exc),
                },
            )
            return

        answer = "".join(answer_parts)
        assistant_message.content_markdown = answer
        assistant_message.status = "completed"
        self.session.add(assistant_message)
        citations = self._create_citations(
            message_id=assistant_message.id,
            results=search_response.results,
        )
        self.session.commit()

        yield _sse(
            "citations",
            {
                "message_id": str(assistant_message.id),
                "citations": [_citation_payload(citation, index=index) for index, citation in enumerate(citations)],
            },
        )
        yield _sse(
            "done",
            {"message_id": str(assistant_message.id), "status": "completed"},
        )

    def _attach_retrieval_contexts(self, retrieval_run_id: UUID, message_id: UUID) -> None:
        self.session.execute(
            update(RetrievedContext)
            .where(RetrievedContext.retrieval_run_id == retrieval_run_id)
            .values(chat_message_id=message_id, used_in_answer=True)
        )
        self.session.commit()

    def _create_citations(self, *, message_id: UUID, results: list[SearchResultItem]) -> list[Citation]:
        citations: list[Citation] = []
        for index, result in enumerate(results, start=1):
            if result.result_type != "chunk":
                continue
            citation = Citation(
                target_type="chat_message",
                target_id=message_id,
                file_id=UUID(str(result.source["file_id"])) if result.source.get("file_id") else None,
                chunk_id=result.result_id,
                knowledge_unit_id=None,
                source_span_id=(
                    UUID(str(result.source["source_span_id"]))
                    if result.source.get("source_span_id")
                    else None
                ),
                label=f"S{index}",
                preview_text=result.preview_text,
                source_available=bool(result.source.get("source_available")),
                created_at=utcnow(),
            )
            self.session.add(citation)
            citations.append(citation)
        self.session.flush()
        return citations


def _sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _chat_messages(*, question: str, results: list[SearchResultItem]) -> list[dict[str, str]]:
    evidence_lines = []
    for index, result in enumerate(results, start=1):
        source = result.source
        location_parts = []
        if source.get("file_name"):
            location_parts.append(str(source["file_name"]))
        if source.get("line_start") and source.get("line_end"):
            location_parts.append(f"lines {source['line_start']}-{source['line_end']}")
        location = ", ".join(location_parts) or result.title
        evidence_lines.append(f"[S{index}] {location}: {result.preview_text}")

    evidence = "\n".join(evidence_lines) if evidence_lines else "No retrieved evidence was found."
    return [
        {
            "role": "system",
            "content": (
                "You are KnowWeave's evidence-grounded assistant. Answer using the retrieved "
                "evidence when it is relevant. Cite evidence labels like [S1]. If the evidence "
                "is insufficient, say what is missing instead of inventing facts."
            ),
        },
        {
            "role": "user",
            "content": f"Question:\n{question}\n\nRetrieved evidence:\n{evidence}",
        },
    ]


def _search_result_payload(item: SearchResultItem) -> dict[str, object]:
    return {
        "result_id": str(item.result_id),
        "result_type": item.result_type,
        "title": item.title,
        "preview_text": item.preview_text,
        "score": str(item.score),
        "rank": item.rank,
        "source": item.source,
        "status": item.status,
        "metadata": item.metadata,
    }


def _provider_name(provider: LLMProvider) -> str:
    return str(getattr(provider, "provider_name", "unknown"))


def _provider_model_name(provider: LLMProvider) -> str | None:
    model_name = getattr(provider, "model_name", None)
    return str(model_name) if model_name is not None else None


def _citation_payload(citation: Citation, *, index: int) -> dict[str, object]:
    return {
        "key": citation.label or f"S{index + 1}",
        "label": citation.label,
        "file_id": str(citation.file_id) if citation.file_id else None,
        "chunk_id": str(citation.chunk_id) if citation.chunk_id else None,
        "source_span_id": str(citation.source_span_id) if citation.source_span_id else None,
        "preview_text": citation.preview_text,
        "source_available": citation.source_available,
    }
