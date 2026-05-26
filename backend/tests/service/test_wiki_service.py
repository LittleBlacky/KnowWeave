from __future__ import annotations

import pytest
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import make_engine
from app.providers.storage import LocalStorageProvider
from app.services.chunk_service import ChunkService
from app.services.file_service import FileService
from app.services.parsing_service import ParsingService
from app.services.wiki_service import WikiChangeSummaryRequiredError, WikiService


def _session_factory(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'wiki-service.db'}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def _seed_file_and_chunks(tmp_path, session):
    storage = LocalStorageProvider(tmp_path / "files")
    file_record = FileService(session=session, storage=storage).create_file(
        filename="policy.md",
        content_type="text/markdown",
        content=b"# Policy\n\nLeave requests require manager approval.",
    )
    ParsingService(session=session, storage=storage).parse_file(file_record.id)
    chunks = ChunkService(session=session).build_chunks_for_file(file_record.id)
    return file_record, chunks


def test_wiki_service_generates_document_wiki_draft_with_chunk_citations(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)

    with SessionLocal() as session:
        file_record, chunks = _seed_file_and_chunks(tmp_path, session)
        service = WikiService(session=session)

        wiki = service.generate_document_wiki(file_record.id)
        citations = service.list_wiki_citations(wiki.id)

        assert wiki.title == "policy.md"
        assert wiki.wiki_type == "document_wiki"
        assert wiki.status == "draft"
        assert wiki.source_file_id == file_record.id
        assert "Leave requests require manager approval." in wiki.content_markdown
        assert len(citations) == 1
        assert citations[0].target_type == "wiki_page"
        assert citations[0].target_id == wiki.id
        assert citations[0].chunk_id == chunks[0].id
        assert citations[0].source_span_id is not None
        assert citations[0].source_available is True


def test_wiki_service_requires_change_summary_when_editing(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)

    with SessionLocal() as session:
        file_record, _ = _seed_file_and_chunks(tmp_path, session)
        service = WikiService(session=session)
        wiki = service.generate_document_wiki(file_record.id)

        with pytest.raises(WikiChangeSummaryRequiredError):
            service.update_wiki(
                wiki.id,
                content_markdown="Updated policy content.",
                change_summary="",
            )

        updated = service.update_wiki(
            wiki.id,
            content_markdown="Updated policy content.",
            change_summary="Clarified manager approval policy.",
            status="verified",
        )

        assert updated.content_markdown == "Updated policy content."
        assert updated.status == "verified"
        assert updated.metadata_["last_change_summary"] == "Clarified manager approval policy."
