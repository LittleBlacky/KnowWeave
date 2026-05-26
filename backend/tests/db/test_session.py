from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.db.session import make_engine


def test_database_session_can_open_and_close(tmp_path) -> None:
    engine = make_engine(f"sqlite:///{tmp_path / 'session.db'}")
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    try:
        with TestingSessionLocal() as session:
            assert session.execute(text("select 1")).scalar_one() == 1
    finally:
        engine.dispose()
