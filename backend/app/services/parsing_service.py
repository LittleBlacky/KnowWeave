from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.base import utcnow
from app.models.files import DocumentBlock, KnowledgeFile, ParseResult
from app.providers.parsers import DocxTextParser, MarkdownParser, PdfTextParser, TextParser
from app.providers.parsers.base import DocumentParser, ParserResult
from app.providers.storage import LocalStorageProvider, StoredFileNotFoundError
from app.services.file_service import FileNotFoundError as KnowledgeFileNotFoundError

NEEDS_REVIEW_WARNING_CODES = {"LOW_TEXT_COVERAGE", "GARBLED_TEXT_SUSPECTED", "MISSING_PAGE_POSITION"}


class ParserNotFoundError(AppError):
    def __init__(self, file_type: str) -> None:
        super().__init__(
            code="PARSER_NOT_FOUND",
            message="No parser is available for this file type.",
            status_code=400,
            details={"file_type": file_type},
        )


class ParsingService:
    def __init__(self, *, session: Session, storage: LocalStorageProvider) -> None:
        self.session = session
        self.storage = storage
        self.parsers: dict[str, DocumentParser] = {
            "txt": TextParser(),
            "md": MarkdownParser(),
            "markdown": MarkdownParser(),
            "pdf": PdfTextParser(),
            "docx": DocxTextParser(),
        }

    def parse_file(self, file_id: UUID) -> ParseResult:
        file_record = self.session.get(KnowledgeFile, file_id)
        if file_record is None or file_record.deleted_at is not None:
            raise KnowledgeFileNotFoundError()

        parser = self.parsers.get(file_record.file_type)
        if parser is None:
            raise ParserNotFoundError(file_record.file_type)

        file_record.status = "parsing"
        self.session.add(file_record)
        self.session.flush()

        try:
            content = self.storage.read(file_record.storage_path)
        except StoredFileNotFoundError:
            return self._record_failure(
                file_record=file_record,
                parser=parser,
                error_message="Stored file content was not found.",
            )

        try:
            parsed = parser.parse(content, filename=file_record.original_filename)
        except Exception as exc:  # pragma: no cover - defensive boundary for provider failures.
            return self._record_failure(
                file_record=file_record,
                parser=parser,
                error_message=str(exc) or exc.__class__.__name__,
            )

        return self._record_success(file_record=file_record, parsed=parsed)

    def list_blocks(self, file_id: UUID) -> list[DocumentBlock]:
        file_record = self.session.get(KnowledgeFile, file_id)
        if file_record is None or file_record.deleted_at is not None:
            raise KnowledgeFileNotFoundError()
        statement = (
            select(DocumentBlock)
            .where(DocumentBlock.file_id == file_id)
            .order_by(DocumentBlock.block_index.asc())
        )
        return list(self.session.scalars(statement).all())

    def _record_success(self, *, file_record: KnowledgeFile, parsed: ParserResult) -> ParseResult:
        has_empty_output = any(w.code == "PARSER_OUTPUT_EMPTY" for w in parsed.warnings)
        has_blocks = len(parsed.blocks) > 0
        if has_empty_output or not has_blocks:
            status = "parse_failed"
        else:
            status = "parse_succeeded"

        parse_result = ParseResult(
            file_id=file_record.id,
            parser_name=parsed.parser_name,
            parser_version=parsed.parser_version,
            status=status,
            raw_text=parsed.raw_text,
            warnings=[
                {"code": warning.code, "message": warning.message} for warning in parsed.warnings
            ],
            error_message=None,
            parse_metadata=parsed.metadata,
            created_at=utcnow(),
        )
        self.session.add(parse_result)
        self.session.flush()

        for parsed_block in parsed.blocks:
            block_metadata = dict(parsed_block.metadata)
            block_metadata["position"] = {
                "line_start": parsed_block.position.line_start,
                "line_end": parsed_block.position.line_end,
            }
            self.session.add(
                DocumentBlock(
                    file_id=file_record.id,
                    parse_result_id=parse_result.id,
                    parent_block_id=None,
                    block_index=parsed_block.block_index,
                    block_type=parsed_block.block_type,
                    raw_content=parsed_block.raw_content,
                    normalized_content=parsed_block.normalized_content,
                    is_ignored=False,
                    page_number=parsed_block.position.page_number,
                    char_start=parsed_block.position.char_start,
                    char_end=parsed_block.position.char_end,
                    bbox=None,
                    asset_ref=None,
                    context_before=None,
                    context_after=None,
                    metadata_=block_metadata,
                    created_at=utcnow(),
                )
            )

        warning_codes = {warning.code for warning in parsed.warnings}
        if not has_blocks or has_empty_output:
            file_record.status = "parse_failed"
        elif warning_codes & NEEDS_REVIEW_WARNING_CODES:
            file_record.status = "parse_needs_review"
        else:
            file_record.status = "parse_succeeded"
        self.session.add(file_record)
        self.session.commit()
        self.session.refresh(parse_result)
        self.session.refresh(file_record)
        return parse_result

    def _record_failure(
        self,
        *,
        file_record: KnowledgeFile,
        parser: DocumentParser,
        error_message: str,
    ) -> ParseResult:
        parse_result = ParseResult(
            file_id=file_record.id,
            parser_name=parser.parser_name,
            parser_version=parser.parser_version,
            status="parse_failed",
            raw_text="",
            warnings=[],
            error_message=error_message,
            parse_metadata={},
            created_at=utcnow(),
        )
        file_record.status = "parse_failed"
        self.session.add_all([parse_result, file_record])
        self.session.commit()
        self.session.refresh(parse_result)
        self.session.refresh(file_record)
        return parse_result
