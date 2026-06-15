from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.chat import ChatMessage, Citation, RetrievedContext
from app.models.feedback import EvaluationSample, Feedback


class EvaluationSampleNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="EVALUATION_SAMPLE_NOT_FOUND",
            message="Evaluation sample not found.",
            status_code=404,
        )


class EvaluationSourceNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="EVALUATION_SOURCE_NOT_FOUND",
            message="Evaluation source was not found.",
            status_code=404,
        )


class EvaluationService:
    def __init__(self, *, session: Session) -> None:
        self.session = session

    def create_manual_candidate(
        self,
        *,
        question: str,
        expected_answer: str | None = None,
        expected_source_files: list[UUID] | None = None,
        expected_source_chunks: list[UUID] | None = None,
        created_from: str = "manual",
        status: str = "candidate",
        difficulty: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> EvaluationSample:
        sample = EvaluationSample(
            question=question,
            expected_answer=expected_answer,
            expected_source_files=_uuid_strings(expected_source_files or []),
            expected_source_chunks=_uuid_strings(expected_source_chunks or []),
            created_from=created_from,
            source_chat_message_id=None,
            source_feedback_id=None,
            status=status,
            difficulty=difficulty,
            metadata_=metadata or {},
        )
        self.session.add(sample)
        self.session.commit()
        self.session.refresh(sample)
        return sample

    def list_samples(self, *, status: str | None = None) -> list[EvaluationSample]:
        statement = select(EvaluationSample).order_by(EvaluationSample.created_at.desc())
        if status is not None:
            statement = statement.where(EvaluationSample.status == status)
        return list(self.session.scalars(statement).all())

    def get_sample(self, sample_id: UUID) -> EvaluationSample:
        sample = self.session.get(EvaluationSample, sample_id)
        if sample is None:
            raise EvaluationSampleNotFoundError()
        return sample

    def create_candidate_from_feedback(self, feedback_id: UUID) -> EvaluationSample:
        feedback = self.session.get(Feedback, feedback_id)
        if feedback is None:
            raise EvaluationSourceNotFoundError()

        source_message = self._source_message_for_feedback(feedback)
        citations = self._citations_for_message(source_message.id) if source_message else []
        expected_source_files = _unique_uuids(
            [citation.file_id for citation in citations if citation.file_id is not None]
        )
        expected_source_chunks = _unique_uuids(
            [citation.chunk_id for citation in citations if citation.chunk_id is not None]
        )

        if feedback.target_type == "chunk":
            expected_source_chunks = _unique_uuids([feedback.target_id, *expected_source_chunks])
        if feedback.target_type == "citation":
            citation = self.session.get(Citation, feedback.target_id)
            if citation is not None:
                expected_source_files = _unique_uuids([citation.file_id, *expected_source_files])
                expected_source_chunks = _unique_uuids([citation.chunk_id, *expected_source_chunks])

        sample = EvaluationSample(
            question=self._question_for_message(source_message) or feedback.comment or "Feedback candidate",
            expected_answer=source_message.content_markdown if source_message else None,
            expected_source_files=_uuid_strings(expected_source_files),
            expected_source_chunks=_uuid_strings(expected_source_chunks),
            created_from="feedback",
            source_chat_message_id=source_message.id if source_message else None,
            source_feedback_id=feedback.id,
            status="candidate",
            difficulty=None,
            metadata_={
                "feedback_snapshot": _feedback_snapshot(feedback),
                "expected_source_hint": feedback.metadata_.get("expected_source_hint"),
                "retrieved_contexts_snapshot": (
                    self._retrieved_context_snapshots(source_message.id) if source_message else []
                ),
                "citations_snapshot": [_citation_snapshot(citation) for citation in citations],
            },
        )
        self.session.add(sample)
        self.session.commit()
        self.session.refresh(sample)
        return sample

    def create_candidate_from_chat_message(self, message_id: UUID) -> EvaluationSample:
        message = self.session.get(ChatMessage, message_id)
        if message is None:
            raise EvaluationSourceNotFoundError()

        retrieved_contexts = self._retrieved_contexts_for_message(message_id)
        citations = self._citations_for_message(message_id)
        sample = EvaluationSample(
            question=self._question_for_message(message) or "",
            expected_answer=message.content_markdown,
            expected_source_files=_uuid_strings(
                _unique_uuids([citation.file_id for citation in citations if citation.file_id is not None])
            ),
            expected_source_chunks=_uuid_strings(
                _unique_uuids(
                    [
                        *[context.result_id for context in retrieved_contexts if context.result_type == "chunk"],
                        *[citation.chunk_id for citation in citations if citation.chunk_id is not None],
                    ]
                )
            ),
            created_from="chat_message",
            source_chat_message_id=message.id,
            source_feedback_id=None,
            status="candidate",
            difficulty=None,
            metadata_={
                "retrieved_contexts_snapshot": [
                    _retrieved_context_snapshot(context) for context in retrieved_contexts
                ],
                "citations_snapshot": [_citation_snapshot(citation) for citation in citations],
            },
        )
        self.session.add(sample)
        self.session.commit()
        self.session.refresh(sample)
        return sample

    def _source_message_for_feedback(self, feedback: Feedback) -> ChatMessage | None:
        if feedback.target_type == "chat_message":
            return self.session.get(ChatMessage, feedback.target_id)
        if feedback.target_type == "citation":
            citation = self.session.get(Citation, feedback.target_id)
            if citation is not None and citation.target_type == "chat_message":
                return self.session.get(ChatMessage, citation.target_id)
        return None

    def _question_for_message(self, message: ChatMessage | None) -> str | None:
        if message is None:
            return None
        statement = (
            select(ChatMessage)
            .where(ChatMessage.session_id == message.session_id)
            .where(ChatMessage.role == "user")
            .where(ChatMessage.created_at <= message.created_at)
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        question = self.session.scalar(statement)
        return question.content_markdown if question is not None else None

    def _retrieved_contexts_for_message(self, message_id: UUID) -> list[RetrievedContext]:
        statement = (
            select(RetrievedContext)
            .where(RetrievedContext.chat_message_id == message_id)
            .order_by(RetrievedContext.rank.asc())
        )
        return list(self.session.scalars(statement).all())

    def _retrieved_context_snapshots(self, message_id: UUID) -> list[dict[str, object]]:
        return [_retrieved_context_snapshot(context) for context in self._retrieved_contexts_for_message(message_id)]

    def run_metrics(self) -> dict[str, object]:
        """Compute basic evaluation metrics across all candidate samples."""
        samples = self.list_samples()
        total = len(samples)
        if total == 0:
            return {"total_samples": 0, "message": "No evaluation samples available."}

        verified = sum(1 for s in samples if s.status == "verified")
        candidates = sum(1 for s in samples if s.status == "candidate")
        with_answer = sum(1 for s in samples if s.expected_answer)
        with_sources = sum(
            1 for s in samples
            if (s.expected_source_files and len(s.expected_source_files) > 0)
            or (s.expected_source_chunks and len(s.expected_source_chunks) > 0)
        )

        return {
            "total_samples": total,
            "verified": verified,
            "candidates": candidates,
            "with_answer": with_answer,
            "with_sources": with_sources,
            "source_traceability_pct": round(with_sources / total * 100, 1) if total > 0 else 0,
            "answer_coverage_pct": round(with_answer / total * 100, 1) if total > 0 else 0,
        }

    def _citations_for_message(self, message_id: UUID) -> list[Citation]:
        statement = (
            select(Citation)
            .where(Citation.target_type == "chat_message")
            .where(Citation.target_id == message_id)
            .order_by(Citation.created_at.asc())
        )
        return list(self.session.scalars(statement).all())


def _feedback_snapshot(feedback: Feedback) -> dict[str, object]:
    return {
        "id": str(feedback.id),
        "target_type": feedback.target_type,
        "target_id": str(feedback.target_id),
        "feedback_type": feedback.feedback_type,
        "comment": feedback.comment,
        "metadata": feedback.metadata_,
    }


def _retrieved_context_snapshot(context: RetrievedContext) -> dict[str, object]:
    return {
        "id": str(context.id),
        "retrieval_run_id": str(context.retrieval_run_id),
        "result_type": context.result_type,
        "result_id": str(context.result_id),
        "rank": context.rank,
        "score": str(context.score) if context.score is not None else None,
        "retrieval_strategy": context.retrieval_strategy,
        "used_in_answer": context.used_in_answer,
    }


def _citation_snapshot(citation: Citation) -> dict[str, object]:
    return {
        "id": str(citation.id),
        "label": citation.label,
        "file_id": str(citation.file_id) if citation.file_id else None,
        "chunk_id": str(citation.chunk_id) if citation.chunk_id else None,
        "source_span_id": str(citation.source_span_id) if citation.source_span_id else None,
        "preview_text": citation.preview_text,
        "source_available": citation.source_available,
    }


def _unique_uuids(values: list[UUID | None]) -> list[UUID]:
    seen: set[UUID] = set()
    unique: list[UUID] = []
    for value in values:
        if value is None or value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique


def _uuid_strings(values: list[UUID]) -> list[str]:
    return [str(value) for value in values]
