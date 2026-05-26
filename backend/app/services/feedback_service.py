from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.chat import ChatMessage, Citation, RetrievedContext
from app.models.feedback import Feedback
from app.models.files import Chunk
from app.models.knowledge import KnowledgeUnit
from app.models.wiki import WikiPage

SUPPORTED_TARGETS = {
    "chat_message": ChatMessage,
    "retrieved_context": RetrievedContext,
    "citation": Citation,
    "chunk": Chunk,
    "knowledge_unit": KnowledgeUnit,
    "wiki_page": WikiPage,
}

SUPPORTED_FEEDBACK_TYPES = {
    "answer_helpful",
    "answer_wrong",
    "citation_helpful",
    "citation_wrong",
    "retrieval_helpful",
    "retrieval_irrelevant",
    "retrieval_missing",
    "chunk_low_quality",
    "wiki_needs_update",
}


class FeedbackInvalidTargetTypeError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="FEEDBACK_INVALID_TARGET_TYPE",
            message="Feedback target_type is not supported.",
            status_code=400,
        )


class FeedbackInvalidTypeError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="FEEDBACK_INVALID_TYPE",
            message="Feedback type is not supported.",
            status_code=400,
        )


class FeedbackTargetNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="FEEDBACK_TARGET_NOT_FOUND",
            message="Feedback target was not found.",
            status_code=404,
        )


class FeedbackService:
    def __init__(self, *, session: Session) -> None:
        self.session = session

    def create_feedback(
        self,
        *,
        target_type: str,
        target_id: UUID,
        feedback_type: str,
        comment: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> Feedback:
        self._validate_target(target_type, target_id)
        if feedback_type not in SUPPORTED_FEEDBACK_TYPES:
            raise FeedbackInvalidTypeError()

        feedback = Feedback(
            target_type=target_type,
            target_id=target_id,
            feedback_type=feedback_type,
            comment=comment,
            status="open",
            metadata_=metadata or {},
        )
        self.session.add(feedback)
        self.session.commit()
        self.session.refresh(feedback)
        return feedback

    def list_feedback(self, *, target_type: str | None = None) -> list[Feedback]:
        from sqlalchemy import select

        statement = select(Feedback)
        if target_type is not None:
            statement = statement.where(Feedback.target_type == target_type)
        statement = statement.order_by(Feedback.created_at.desc())
        return list(self.session.scalars(statement).all())

    def _validate_target(self, target_type: str, target_id: UUID) -> None:
        model = SUPPORTED_TARGETS.get(target_type)
        if model is None:
            raise FeedbackInvalidTargetTypeError()
        if self.session.get(model, target_id) is None:
            raise FeedbackTargetNotFoundError()
