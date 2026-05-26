# Data Model: KnowWeave P0 Knowledge Workbench

This file summarizes the executable P0 data model. Detailed field-level guidance remains in `docs/04-data-model-spec.md`.

## Entity: KnowledgeFile

Represents an uploaded original file and immutable evidence source.

**Fields**: id, name, original_filename, file_type, mime_type, size_bytes, sha256, storage_path, directory_path, status, summary, source_note, metadata, deleted_at, created_at, updated_at.

**Relationships**: Has many ParseResult, DocumentBlock, Chunk, SourceSpan, WikiPage and Citation records.

**State rules**: uploaded, queued_for_parse, parsing, parse_succeeded, parse_failed, parse_needs_review, soft_deleted. Soft-deleted files keep history but related chunks are excluded from default retrieval.

## Entity: ParseResult

Represents one parser run for a file.

**Fields**: id, file_id, parser_name, parser_version, status, raw_text, warnings, error_message, parse_metadata, created_at.

**Relationships**: Belongs to KnowledgeFile; produces DocumentBlock records.

## Entity: DocumentBlock

Represents structured extracted content.

**Fields**: id, file_id, parse_result_id, parent_block_id, block_index, block_type, raw_content, normalized_content, is_ignored, page_number, char_start, char_end, bbox, asset_ref, context_before, context_after, metadata, created_at.

**Relationships**: Belongs to KnowledgeFile and ParseResult; may produce Chunks.

## Entity: Chunk

Represents governable evidence used by retrieval, Wiki and citations.

**Fields**: id, file_id, parse_result_id, document_block_id, parent_chunk_id, chunk_index, chunk_type, raw_content, edited_content, is_manually_edited, summary, status, quality_signals, token_count, char_count, search_text, metadata, is_searchable, created_at, updated_at.

**Relationships**: Belongs to KnowledgeFile and optionally DocumentBlock; has many SourceSpan and Citation records; supports KnowledgeUnit sources.

**State rules**: draft, needs_review, verified, ignored, archived. ignored and archived set is_searchable false by default.

## Entity: SourceSpan

Represents source locator data for chunks and citations.

**Fields**: id, file_id, chunk_id, document_block_id, page_number, char_start, char_end, line_start, line_end, column_start, column_end, bbox, selector, preview_text, created_at.

**Validation**: Must include at least one locator form: document block, page, line, char range, bbox, selector or preview text.

## Entity: KnowledgeUnit

Represents curated atomic knowledge.

**Fields**: id, title, unit_type, content, summary, status, trust_level, applicable_scope, created_from, search_text, metadata, created_at, updated_at, verified_at, archived_at.

**Relationships**: Has many KnowledgeUnitSource records; can be cited by Wiki and Chat.

**State rules**: draft, pending_review, verified, archived. AI-generated units default to draft or pending_review.

## Entity: KnowledgeUnitSource

Represents the evidence relationship behind a Knowledge Unit.

**Fields**: id, knowledge_unit_id, file_id, chunk_id, source_span_id, source_type, source_label, source_available, created_at.

**Validation**: Verified Knowledge Units should have at least one explainable source unless they are explicitly manual knowledge.

## Entity: WikiPage

Represents long-lived LLM Wiki content.

**Fields**: id, title, wiki_type, status, summary, content_markdown, source_file_id, generation_prompt_version, search_text, metadata, created_at, updated_at, verified_at.

**Relationships**: May belong to KnowledgeFile; has many WikiPageUnit and Citation records.

**State rules**: P0 requires document_wiki. Edits require change_summary and may create revision snapshots in P1.

## Entity: WikiPageUnit

Represents the organization relationship between a Wiki page and Knowledge Units.

**Fields**: id, wiki_page_id, knowledge_unit_id, section_anchor, sort_order, created_at.

**Validation**: Document Wiki pages may organize relevant Knowledge Units, but citations remain the authoritative source evidence for claims.

## Entity: Citation

Represents a claim-to-source relationship.

**Fields**: id, target_type, target_id, file_id, chunk_id, knowledge_unit_id, source_span_id, label, preview_text, source_available, created_at.

**Validation**: Must include at least one source reference: chunk, knowledge unit, source span or manual metadata.

## Entity: ChatSession and ChatMessage

Represent conversation state and final persisted messages.

**ChatSession Fields**: id, title, scope, created_at, updated_at.

**ChatMessage Fields**: id, session_id, role, content_markdown, status, model_provider, model_name, prompt_version, created_at.

**State rules**: assistant message status may be completed, failed or partial.

## Entity: RetrievedContext

Represents Search or Chat retrieval output.

**Fields**: id, retrieval_run_id, chat_message_id, query_text, result_type, result_id, rank, score, retrieval_strategy, retrieval_params, used_in_answer, created_at.

**Validation**: All contexts for one Search or Chat retrieval share one retrieval_run_id.

## Entity: Feedback

Represents user feedback on evidence or generated content.

**Fields**: id, target_type, target_id, feedback_type, comment, metadata, created_at.

**Targets**: chat_message, retrieved_context, citation, wiki_page, chunk.

## Entity: EvaluationSample

Represents candidate or curated evaluation item.

**Fields**: id, question, expected_answer, expected_source_files, expected_source_chunks, created_from, source_chat_message_id, status, difficulty, metadata, created_at, updated_at.

**State rules**: candidate, draft, verified, rejected, archived.

## Entity: Tag and TagBinding

Represent lightweight organization metadata.

**Tag Fields**: id, name, description, color, created_at.

**TagBinding Fields**: id, tag_id, target_type, target_id, created_at.

**Targets**: file, knowledge_unit, wiki_page.
