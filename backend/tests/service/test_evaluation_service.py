from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import make_engine
from app.models.chat import ChatMessage, Citation, RetrievedContext
from app.providers.storage import LocalStorageProvider
from app.services.chat_service import ChatService
from app.services.chunk_service import ChunkService
from app.services.evaluation_service import EvaluationService
from app.services.feedback_service import FeedbackService
from app.services.file_service import FileService
from app.services.parsing_service import ParsingService


def _session_factory(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'evaluation-service.db'}")
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


def _seed_chat_message(tmp_path, session) -> ChatMessage:
    _seed_chunk(tmp_path, session)
    service = ChatService(session=session)
    chat_session = service.create_session(title="Policy Q&A")
    events = []

    async def collect_events() -> None:
        async for event in service.stream_answer(
            session_id=chat_session.id,
            question="Who approves leave requests?",
            top_k=1,
        ):
            events.append(event)

    asyncio.run(collect_events())
    message_id = next(line for event in events for line in event.splitlines() if line.startswith("data: "))
    raw_message_id = message_id.split('"message_id": "')[1].split('"')[0]
    return session.get(ChatMessage, raw_message_id)


def test_evaluation_service_creates_candidate_from_citation_feedback(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)

    with SessionLocal() as session:
        message = _seed_chat_message(tmp_path, session)
        citation = session.scalar(
            select(Citation)
            .where(Citation.target_type == "chat_message")
            .where(Citation.target_id == message.id)
        )
        feedback = FeedbackService(session=session).create_feedback(
            target_type="citation",
            target_id=citation.id,
            feedback_type="citation_wrong",
            comment="The cited chunk does not mention approver scope.",
            metadata={"expected_source_hint": "Manager approval section"},
        )

        sample = EvaluationService(session=session).create_candidate_from_feedback(feedback.id)

        assert sample.status == "candidate"
        assert sample.created_from == "feedback"
        assert sample.source_feedback_id == feedback.id
        assert sample.source_chat_message_id == message.id
        assert sample.expected_source_chunks == [citation.chunk_id]
        assert sample.metadata_["feedback_snapshot"]["feedback_type"] == "citation_wrong"
        assert sample.metadata_["feedback_snapshot"]["comment"] == feedback.comment
        assert sample.metadata_["expected_source_hint"] == "Manager approval section"


def test_evaluation_service_creates_candidate_from_chat_message_with_snapshots(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)

    with SessionLocal() as session:
        message = _seed_chat_message(tmp_path, session)

        sample = EvaluationService(session=session).create_candidate_from_chat_message(message.id)

        assert sample.question == "Who approves leave requests?"
        assert sample.expected_answer.startswith("Fake answer:")
        assert sample.created_from == "chat_message"
        assert sample.source_chat_message_id == message.id
        assert sample.status == "candidate"
        assert sample.expected_source_files
        assert sample.expected_source_chunks
        assert sample.metadata_["retrieved_contexts_snapshot"][0]["used_in_answer"] is True
        assert sample.metadata_["citations_snapshot"][0]["label"] == "S1"
