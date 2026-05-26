from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import make_engine
from app.models.files import Chunk, KnowledgeFile, ParseResult
from app.providers.storage import LocalStorageProvider
from app.services.demo_seed_service import seed_demo_data


def _session_factory(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'seed-demo-data.db'}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def test_seed_demo_data_uploads_parses_and_chunks_demo_fixtures(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)
    demo_dir = Path(__file__).resolve().parents[3] / "data" / "demo"

    with SessionLocal() as session:
        result = seed_demo_data(
            session=session,
            storage=LocalStorageProvider(tmp_path / "files"),
            demo_dir=demo_dir,
        )

        assert result.file_count == 4
        assert result.parse_count == 4
        assert result.chunk_count >= 4
        assert sorted(item.filename for item in result.files) == [
            "company_policy.md",
            "notes.txt",
            "security_handbook.pdf",
            "team_faq.docx",
        ]
        assert session.query(KnowledgeFile).count() == 4
        assert session.query(ParseResult).count() == 4
        assert session.query(Chunk).count() == result.chunk_count
