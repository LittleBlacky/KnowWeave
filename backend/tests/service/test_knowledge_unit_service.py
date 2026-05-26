from __future__ import annotations

import pytest
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import make_engine
from app.providers.storage import LocalStorageProvider
from app.services.chunk_service import ChunkService
from app.services.file_service import FileService
from app.services.knowledge_unit_service import (
    KnowledgeUnitVerifiedSourceRequiredError,
    KnowledgeUnitService,
)
from app.services.parsing_service import ParsingService
from app.services.tag_service import TagService


def _session_factory(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'knowledge-unit-service.db'}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def _seed_file_and_chunk(tmp_path, session):
    storage = LocalStorageProvider(tmp_path / "files")
    file_record = FileService(session=session, storage=storage).create_file(
        filename="policy.md",
        content_type="text/markdown",
        content=b"# Policy\n\nLeave requests require manager approval.",
    )
    ParsingService(session=session, storage=storage).parse_file(file_record.id)
    chunk = ChunkService(session=session).build_chunks_for_file(file_record.id)[0]
    return file_record, chunk


def test_knowledge_unit_service_creates_unit_with_chunk_source_and_tags(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)

    with SessionLocal() as session:
        file_record, chunk = _seed_file_and_chunk(tmp_path, session)
        tag = TagService(session=session).create_tag(name="HR", description="People policy")

        unit = KnowledgeUnitService(session=session).create_knowledge_unit(
            title="Leave approval rule",
            unit_type="rule",
            content="Leave requests require manager approval.",
            summary="Manager approval is required.",
            status="pending_review",
            applicable_scope="HR policies",
            source_chunk_ids=[chunk.id],
            tag_ids=[tag.id],
        )

        sources = KnowledgeUnitService(session=session).list_sources(unit.id)
        units = KnowledgeUnitService(session=session).list_knowledge_units(
            tag="HR",
            source_file_id=file_record.id,
            unit_type="rule",
            status="pending_review",
        )

        assert unit.created_from == "chunk"
        assert unit.search_text == (
            "Leave approval rule\n"
            "Manager approval is required.\n"
            "Leave requests require manager approval."
        )
        assert sources[0].knowledge_unit_id == unit.id
        assert sources[0].file_id == file_record.id
        assert sources[0].chunk_id == chunk.id
        assert sources[0].source_span_id is not None
        assert sources[0].source_type == "chunk"
        assert sources[0].source_available is True
        assert [item.id for item in units] == [unit.id]


def test_knowledge_unit_service_requires_source_for_verified_units(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)

    with SessionLocal() as session:
        service = KnowledgeUnitService(session=session)

        with pytest.raises(KnowledgeUnitVerifiedSourceRequiredError):
            service.create_knowledge_unit(
                title="Unbacked approval rule",
                unit_type="rule",
                content="Managers approve all leave.",
                status="verified",
            )


def test_knowledge_unit_service_updates_status_content_sources_and_tags(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)

    with SessionLocal() as session:
        _, chunk = _seed_file_and_chunk(tmp_path, session)
        tag_service = TagService(session=session)
        original_tag = tag_service.create_tag(name="Draft")
        updated_tag = tag_service.create_tag(name="Verified")
        service = KnowledgeUnitService(session=session)
        unit = service.create_knowledge_unit(
            title="Leave approval",
            unit_type="rule",
            content="Leave needs approval.",
            tag_ids=[original_tag.id],
        )

        updated = service.update_knowledge_unit(
            unit.id,
            title="Leave approval rule",
            content="Leave requests require manager approval.",
            status="verified",
            source_chunk_ids=[chunk.id],
            tag_ids=[updated_tag.id],
        )

        assert updated.title == "Leave approval rule"
        assert updated.status == "verified"
        assert updated.verified_at is not None
        assert service.list_sources(updated.id)[0].chunk_id == chunk.id
        assert [item.id for item in service.list_knowledge_units(tag="Verified")] == [updated.id]
        assert service.list_knowledge_units(tag="Draft") == []
