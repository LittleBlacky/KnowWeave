from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import make_engine
from app.models.files import DocumentBlock, ParseResult
from app.providers.storage import LocalStorageProvider
from app.services.file_service import FileService
from app.services.parsing_service import ParsingService


def _session_factory(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'parse-service.db'}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def test_parse_service_persists_parse_result_and_document_blocks(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)
    storage = LocalStorageProvider(tmp_path / "files")

    with SessionLocal() as session:
        file_service = FileService(session=session, storage=storage)
        record = file_service.create_file(
            filename="policy.md",
            content_type="text/markdown",
            content=b"# Policy\n\n| Name | Owner |\n| --- | --- |\n| Leave | Ops |",
        )
        service = ParsingService(session=session, storage=storage)

        parse_result = service.parse_file(record.id)

        blocks = session.scalars(
            select(DocumentBlock).where(DocumentBlock.parse_result_id == parse_result.id)
        ).all()
        assert parse_result.status == "parse_succeeded"
        assert parse_result.parser_name == "markdown_parser"
        assert [block.block_type for block in blocks] == ["heading", "table"]
        assert blocks[0].raw_content == "# Policy"
        assert blocks[0].metadata_ == {
            "heading_level": 1,
            "position": {"line_start": 1, "line_end": 1},
        }
        assert blocks[1].metadata_ == {
            "is_placeholder": True,
            "position": {"line_start": 3, "line_end": 5},
        }
        assert parse_result.warnings == [
            {
                "code": "TABLE_AS_PLACEHOLDER",
                "message": "Markdown tables were preserved as placeholder blocks.",
            }
        ]
        assert record.status == "parse_succeeded"


def test_parse_service_records_failure_when_stored_file_is_missing(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)
    storage = LocalStorageProvider(tmp_path / "files")

    with SessionLocal() as session:
        file_service = FileService(session=session, storage=storage)
        record = file_service.create_file(
            filename="notes.txt",
            content_type="text/plain",
            content=b"notes",
        )
        (tmp_path / "files" / record.storage_path).unlink()
        service = ParsingService(session=session, storage=storage)

        parse_result = service.parse_file(record.id)

        assert parse_result.status == "parse_failed"
        assert parse_result.parser_name == "text_parser"
        assert parse_result.error_message == "Stored file content was not found."
        assert record.status == "parse_failed"
        assert session.scalars(select(DocumentBlock)).all() == []
        assert session.scalars(select(ParseResult)).one() is parse_result
