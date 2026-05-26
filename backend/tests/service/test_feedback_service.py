from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import make_engine
from app.models.base import utcnow
from app.models.chat import ChatMessage, ChatSession, Citation
from app.providers.storage import LocalStorageProvider
from app.services.chunk_service import ChunkService
from app.services.feedback_service import (
    FeedbackInvalidTargetTypeError,
    FeedbackService,
    FeedbackTargetNotFoundError,
)
from app.services.file_service import FileService
from app.services.parsing_service import ParsingService
from app.services.wiki_service import WikiService


def _session_factory(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'feedback-service.db'}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def _seed_chunk(tmp_path, session):
    storage = LocalStorageProvider(tmp_path / "files")
    file_record = FileService(session=session, storage=storage).create_file(
        filename="policy.md",
        content_type="text/markdown",
        content=b"# Policy\n\nLeave requests require manager approval.",
    )
    ParsingService(session=session, storage=storage).parse_file(file_record.id)
    return ChunkService(session=session).build_chunks_for_file(file_record.id)[0]


def _seed_message_and_citation(session, chunk):
    chat_session = ChatSession(title="Policy Q&A", scope={})
    session.add(chat_session)
    session.flush()
    message = ChatMessage(
        session_id=chat_session.id,
        role="assistant",
        content_markdown="Leave requests require manager approval.",
        status="completed",
        model_provider="fake",
        model_name="fake-llm",
        prompt_version="chat_qa_v1",
        created_at=utcnow(),
    )
    session.add(message)
    session.flush()
    citation = Citation(
        target_type="chat_message",
        target_id=message.id,
        file_id=chunk.file_id,
        chunk_id=chunk.id,
        knowledge_unit_id=None,
        source_span_id=None,
        label="S1",
        preview_text=chunk.raw_content,
        source_available=True,
        created_at=utcnow(),
    )
    session.add(citation)
    session.commit()
    return message, citation


def test_feedback_service_accepts_supported_feedback_targets(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)

    with SessionLocal() as session:
        chunk = _seed_chunk(tmp_path, session)
        wiki = WikiService(session=session).generate_document_wiki(chunk.file_id)
        message, citation = _seed_message_and_citation(session, chunk)
        service = FeedbackService(session=session)

        created = [
            service.create_feedback(
                target_type="chat_message",
                target_id=message.id,
                feedback_type="answer_wrong",
                comment="The approval owner is incomplete.",
                metadata={"retrieval_run_id": "run_001"},
            ),
            service.create_feedback(
                target_type="citation",
                target_id=citation.id,
                feedback_type="citation_wrong",
                comment="This citation does not support the claim.",
            ),
            service.create_feedback(
                target_type="chunk",
                target_id=chunk.id,
                feedback_type="chunk_low_quality",
                comment="Chunk should be split into policy and exception sections.",
            ),
            service.create_feedback(
                target_type="wiki_page",
                target_id=wiki.id,
                feedback_type="wiki_needs_update",
                comment="Wiki needs a scope section.",
            ),
        ]

        assert [feedback.target_type for feedback in created] == [
            "chat_message",
            "citation",
            "chunk",
            "wiki_page",
        ]
        assert created[0].metadata_["retrieval_run_id"] == "run_001"
        assert created[1].status == "open"


def test_feedback_service_rejects_invalid_or_missing_targets(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)

    with SessionLocal() as session:
        service = FeedbackService(session=session)

        with pytest.raises(FeedbackInvalidTargetTypeError):
            service.create_feedback(
                target_type="unknown",
                target_id=uuid4(),
                feedback_type="answer_wrong",
            )

        with pytest.raises(FeedbackTargetNotFoundError):
            service.create_feedback(
                target_type="chunk",
                target_id=uuid4(),
                feedback_type="chunk_low_quality",
            )
