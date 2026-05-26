from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.files import Chunk, KnowledgeFile, ParseResult
from app.providers.storage import LocalStorageProvider
from app.services.chunk_service import ChunkService
from app.services.file_service import FileService
from app.services.parsing_service import ParsingService


DEMO_FIXTURES = {
    "company_policy.md": "text/markdown",
    "security_handbook.pdf": "application/pdf",
    "team_faq.docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "notes.txt": "text/plain",
}


@dataclass(frozen=True)
class SeededDemoFile:
    filename: str
    file: KnowledgeFile
    parse_result: ParseResult
    chunks: list[Chunk]


@dataclass(frozen=True)
class SeedDemoResult:
    files: list[SeededDemoFile]

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def parse_count(self) -> int:
        return len(self.files)

    @property
    def chunk_count(self) -> int:
        return sum(len(item.chunks) for item in self.files)


def seed_demo_data(
    *,
    session: Session,
    storage: LocalStorageProvider,
    demo_dir: Path,
) -> SeedDemoResult:
    file_service = FileService(session=session, storage=storage)
    parsing_service = ParsingService(session=session, storage=storage)
    chunk_service = ChunkService(session=session)
    seeded: list[SeededDemoFile] = []

    for filename, content_type in DEMO_FIXTURES.items():
        path = demo_dir / filename
        content = path.read_bytes()
        file_record = file_service.create_file(
            filename=filename,
            content_type=content_type,
            content=content,
            directory_path="/demo",
        )
        parse_result = parsing_service.parse_file(file_record.id)
        chunks = chunk_service.build_chunks_for_file(file_record.id)
        seeded.append(
            SeededDemoFile(
                filename=filename,
                file=file_record,
                parse_result=parse_result,
                chunks=chunks,
            )
        )

    return SeedDemoResult(files=seeded)
