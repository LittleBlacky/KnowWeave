from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.files import KnowledgeFile
from app.providers.storage import LocalStorageProvider
from app.services.file_service import FileService, UnsupportedFileTypeError


def _session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'file-service.db'}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def test_file_service_stores_file_and_creates_record(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)
    storage = LocalStorageProvider(tmp_path / "files")

    with SessionLocal() as session:
        service = FileService(session=session, storage=storage)
        record = service.create_file(
            filename="policy.md",
            content_type="text/markdown",
            content=b"# Policy",
            directory_path="/policies",
        )

        assert record.id is not None
        assert record.name == "policy.md"
        assert record.file_type == "md"
        assert record.status == "uploaded"
        assert record.directory_path == "/policies"
        assert len(record.sha256) == 64
        assert (tmp_path / "files" / record.storage_path).read_bytes() == b"# Policy"
        assert session.scalar(select(KnowledgeFile).where(KnowledgeFile.id == record.id)) is record


def test_file_service_rejects_unsupported_file_type(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)
    storage = LocalStorageProvider(tmp_path / "files")

    with SessionLocal() as session:
        service = FileService(session=session, storage=storage)

        try:
            service.create_file(
                filename="payload.exe",
                content_type="application/octet-stream",
                content=b"binary",
            )
        except UnsupportedFileTypeError as exc:
            assert exc.code == "FILE_TYPE_NOT_SUPPORTED"
        else:
            raise AssertionError("UnsupportedFileTypeError was not raised")


def test_file_service_soft_delete_hides_file_from_default_list(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)
    storage = LocalStorageProvider(tmp_path / "files")

    with SessionLocal() as session:
        service = FileService(session=session, storage=storage)
        record = service.create_file(
            filename="notes.txt",
            content_type="text/plain",
            content=b"notes",
        )

        assert service.list_files() == [record]

        service.soft_delete_file(record.id)

        assert service.list_files() == []
        assert service.get_file(record.id, include_deleted=True).status == "soft_deleted"
