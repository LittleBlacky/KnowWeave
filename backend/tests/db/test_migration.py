from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def _alembic_config(database_url: str) -> Config:
    backend_root = Path(__file__).resolve().parents[2]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_alembic_upgrade_head_on_empty_database(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite:///{tmp_path / 'migration.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)

    command.upgrade(_alembic_config(database_url), "head")

    engine = create_engine(database_url)
    try:
      inspector = inspect(engine)
      assert "alembic_version" in inspector.get_table_names()
    finally:
      engine.dispose()


def test_pgvector_init_sql_declares_required_extensions() -> None:
    init_sql = Path(__file__).resolve().parents[3] / "docker" / "postgres" / "init.sql"

    sql = init_sql.read_text(encoding="utf-8")

    assert "CREATE EXTENSION IF NOT EXISTS vector" in sql
    assert "CREATE EXTENSION IF NOT EXISTS pg_trgm" in sql


def test_sqlite_baseline_database_is_queryable_after_migration(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite:///{tmp_path / 'queryable.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)

    command.upgrade(_alembic_config(database_url), "head")

    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            assert connection.execute(text("select 1")).scalar_one() == 1
    finally:
        engine.dispose()
