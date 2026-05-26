from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import make_engine
from app.models.chat import RetrievedContext
from app.providers.storage import LocalStorageProvider
from app.services.chunk_service import ChunkService
from app.services.file_service import FileService
from app.services.knowledge_unit_service import KnowledgeUnitService
from app.services.parsing_service import ParsingService
from app.services.search_service import SearchService
from app.services.wiki_service import WikiService


def _session_factory(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'search-service.db'}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def _build_chunks(tmp_path, session):
    storage = LocalStorageProvider(tmp_path / "files")
    file_record = FileService(session=session, storage=storage).create_file(
        filename="policy.md",
        content_type="text/markdown",
        content=b"# Policy\n\nLeave requests require manager approval.",
    )
    ParsingService(session=session, storage=storage).parse_file(file_record.id)
    return ChunkService(session=session).build_chunks_for_file(file_record.id)


def test_search_service_returns_keyword_chunk_results_and_persists_contexts(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)

    with SessionLocal() as session:
        chunks = _build_chunks(tmp_path, session)
        result = SearchService(session=session).search(query="manager approval", top_k=5)

        contexts = session.scalars(select(RetrievedContext)).all()
        assert result.query == "manager approval"
        assert result.strategy == "keyword"
        assert len(result.results) == 1
        assert result.results[0].result_id == chunks[0].id
        assert result.results[0].result_type == "chunk"
        assert result.results[0].rank == 1
        assert result.results[0].source["file_id"] == str(chunks[0].file_id)
        assert len(contexts) == 1
        assert contexts[0].retrieval_run_id == result.retrieval_run_id
        assert contexts[0].query_text == "manager approval"
        assert contexts[0].result_id == chunks[0].id
        assert contexts[0].used_in_answer is False


def test_search_service_filters_ignored_chunks_from_default_results(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)

    with SessionLocal() as session:
        chunk = _build_chunks(tmp_path, session)[0]
        ChunkService(session=session).ignore_chunk(chunk.id)

        result = SearchService(session=session).search(query="manager approval")

        assert result.results == []
        assert session.scalars(select(RetrievedContext)).all() == []


def test_search_service_can_inspect_retrieval_run(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)

    with SessionLocal() as session:
        _build_chunks(tmp_path, session)
        service = SearchService(session=session)
        result = service.search(query="leave")

        inspected = service.get_retrieval_run(result.retrieval_run_id)

        assert inspected.retrieval_run_id == result.retrieval_run_id
        assert inspected.query == "leave"
        assert [item.result_id for item in inspected.results] == [
            item.result_id for item in result.results
        ]


def test_search_service_searches_file_chunk_knowledge_unit_and_wiki(tmp_path) -> None:
    SessionLocal = _session_factory(tmp_path)

    with SessionLocal() as session:
        chunk = _build_chunks(tmp_path, session)[0]
        unit = KnowledgeUnitService(session=session).create_knowledge_unit(
            title="Leave approval rule",
            unit_type="rule",
            content="Leave requests require manager approval.",
            summary="Manager approval is required.",
            status="pending_review",
            source_chunk_ids=[chunk.id],
        )
        wiki = WikiService(session=session).generate_document_wiki(chunk.file_id)

        result = SearchService(session=session).search(
            query="approval",
            target_types=["file", "chunk", "knowledge_unit", "wiki_page"],
            top_k=10,
        )

        result_ids_by_type = {item.result_type: item.result_id for item in result.results}
        assert result_ids_by_type["file"] == chunk.file_id
        assert result_ids_by_type["chunk"] == chunk.id
        assert result_ids_by_type["knowledge_unit"] == unit.id
        assert result_ids_by_type["wiki_page"] == wiki.id
        contexts = session.scalars(select(RetrievedContext)).all()
        assert {context.result_type for context in contexts} == {
            "file",
            "chunk",
            "knowledge_unit",
            "wiki_page",
        }
