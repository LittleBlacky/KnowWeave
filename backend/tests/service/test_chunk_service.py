from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import make_engine
from app.models.files import Chunk, SourceSpan
from app.providers.storage import LocalStorageProvider
from app.services.chunk_service import ChunkService
from app.services.file_service import FileService
from app.services.parsing_service import ParsingService


def _session_factory(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'chunk-service.db'}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def test_chunk_service_builds_chunks_and_source_spans_after_parse(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)
    storage = LocalStorageProvider(tmp_path / "files")

    with SessionLocal() as session:
        file_service = FileService(session=session, storage=storage)
        file_record = file_service.create_file(
            filename="policy.md",
            content_type="text/markdown",
            content=b"# Policy\n\nLeave requests require manager approval.",
        )
        ParsingService(session=session, storage=storage).parse_file(file_record.id)
        service = ChunkService(session=session)

        chunks = service.build_chunks_for_file(file_record.id)

        spans = session.scalars(select(SourceSpan).where(SourceSpan.chunk_id == chunks[0].id)).all()
        assert len(chunks) == 1
        assert chunks[0].raw_content == "# Policy\n\nLeave requests require manager approval."
        assert chunks[0].status == "draft"
        assert chunks[0].is_searchable is True
        assert chunks[0].search_text == chunks[0].raw_content
        assert spans[0].line_start == 1
        assert spans[0].line_end == 3
        assert spans[0].preview_text == chunks[0].raw_content


def test_chunk_service_excludes_ignored_blocks_from_new_chunks(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)
    storage = LocalStorageProvider(tmp_path / "files")

    with SessionLocal() as session:
        file_record = FileService(session=session, storage=storage).create_file(
            filename="notes.txt",
            content_type="text/plain",
            content=b"Keep this paragraph.\n\nIgnore this paragraph.",
        )
        ParsingService(session=session, storage=storage).parse_file(file_record.id)
        ignored_block = ParsingService(session=session, storage=storage).list_blocks(file_record.id)[1]
        ignored_block.is_ignored = True
        session.add(ignored_block)
        session.commit()

        chunks = ChunkService(session=session).build_chunks_for_file(file_record.id)

        assert [chunk.raw_content for chunk in chunks] == ["Keep this paragraph."]
        assert session.scalars(select(Chunk)).all() == chunks
