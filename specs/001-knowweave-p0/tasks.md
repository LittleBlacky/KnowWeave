# Tasks: KnowWeave P0 Knowledge Workbench

**Input**: Design documents from `/specs/001-knowweave-p0/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi-p0.yaml, quickstart.md

**Tests**: Required. KnowWeave P0 follows TDD as defined by the constitution and `docs/14-tdd-task-breakdown.md`.

**Organization**: Tasks are grouped by setup/foundation and independently testable user stories.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks.
- **[Story]**: Maps implementation tasks to user stories from `spec.md`.
- Every task includes exact file paths.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish local project structure, backend test baseline and Docker/Postgres baseline.

- [X] T001 Create FastAPI app factory and health route in `backend/app/main.py`, `backend/app/api/router.py`, `backend/app/api/v1/health.py`
- [X] T002 [P] Add backend settings tests and default config in `backend/tests/unit/test_settings.py`, `backend/app/core/config.py`
- [X] T003 [P] Add backend health API test in `backend/tests/api/test_health.py`
- [X] T004 Add backend packaging and pytest config in `backend/pyproject.toml`
- [X] T005 Create Postgres compose baseline in `docker-compose.yml`, `docker/postgres/init.sql`, `.env.example`
- [X] T006 [P] Create local dev and health scripts in `scripts/dev-backend.ps1`, `scripts/dev-frontend.ps1`, `scripts/test-compose.ps1`, `scripts/smoke-health.ps1`
- [X] T007 Update ignore rules for secrets, runtime files, caches and generated databases in `.gitignore`

**Validation**:

```powershell
cd backend
python -m pytest tests/api/test_health.py tests/unit/test_settings.py
cd ..
powershell -ExecutionPolicy Bypass -File scripts/test-compose.ps1
```

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database, migrations, frontend shell and shared test infrastructure that block all user stories.

- [X] T008 Add SQLAlchemy base/session and Alembic baseline in `backend/app/db/base.py`, `backend/app/db/session.py`, `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/0001_database_baseline.py`
- [X] T009 [P] Add database migration/session tests in `backend/tests/db/test_migration.py`, `backend/tests/db/test_session.py`
- [X] T010 Create backend shared error/response schema scaffolding in `backend/app/core/errors.py`, `backend/app/schemas/common.py`
- [X] T011 Create backend model package and initial ORM model files in `backend/app/models/`
- [X] T012 Create frontend Next.js app structure and base scripts in `frontend/package.json`, `frontend/tsconfig.json`, `frontend/src/app/page.tsx`
- [X] T013 [P] Configure frontend Vitest, Testing Library and MSW in `frontend/vitest.config.ts`, `frontend/src/test/`
- [X] T014 [P] Implement AppShell and API client baseline in `frontend/src/app-shell/AppShell.tsx`, `frontend/src/shared/api/client.ts`
- [X] T015 [P] Add frontend AppShell/API client tests in `frontend/src/app-shell/AppShell.test.tsx`, `frontend/src/shared/api/client.test.ts`

**Checkpoint**: Foundation ready. No user story work starts until T010-T015 pass.

**Validation**:

```powershell
cd backend
python -m pytest
cd ../frontend
pnpm test
pnpm typecheck
```

---

## Phase 3: User Story 1 - Govern Uploaded Knowledge Evidence (Priority: P1) MVP

**Goal**: Upload files, parse them into blocks, build chunks/source spans and allow chunk governance.

**Independent Test**: Upload a Markdown file, parse it, build chunks, edit one chunk, ignore one chunk and verify source span display without real LLM calls.

### Tests for User Story 1

- [X] T016 [P] [US1] Add upload API contract tests in `backend/tests/api/test_files_upload.py`
- [X] T017 [P] [US1] Add FileService tests for storage and soft delete in `backend/tests/service/test_file_service.py`
- [X] T018 [P] [US1] Add txt, markdown, pdf and docx parser unit tests in `backend/tests/unit/test_text_parser.py`, `backend/tests/unit/test_markdown_parser.py`, `backend/tests/unit/test_pdf_text_parser.py`, `backend/tests/unit/test_docx_text_parser.py`
- [X] T019 [P] [US1] Add parse service/API tests in `backend/tests/service/test_parse_service.py`, `backend/tests/api/test_file_parse.py`
- [X] T020 [P] [US1] Add chunk strategy/service/API tests in `backend/tests/unit/test_chunk_strategy.py`, `backend/tests/service/test_chunk_service.py`, `backend/tests/api/test_chunks.py`
- [X] T021 [P] [US1] Add chunk curation API tests in `backend/tests/api/test_chunk_curation.py`
- [X] T022 [P] [US1] Add frontend file and chunk workspace tests in `frontend/src/features/file-upload/FileUpload.test.tsx`, `frontend/src/features/file-list/FileList.test.tsx`, `frontend/src/features/chunk-workspace/ChunkWorkspace.test.tsx`

### Implementation for User Story 1

- [X] T023 [P] [US1] Create file, parse result, document block, chunk and source span models in `backend/app/models/`
- [X] T024 [US1] Create Alembic migration for files, parsing, chunks and source spans in `backend/alembic/versions/`
- [X] T025 [US1] Implement LocalStorageProvider and FileService in `backend/app/providers/storage.py`, `backend/app/services/file_service.py`
- [X] T026 [US1] Implement file upload/list/detail/delete endpoints in `backend/app/api/v1/files.py`, `backend/app/api/router.py`
- [X] T027 [US1] Implement parser provider interfaces and txt/markdown/pdf/docx parsers in `backend/app/providers/parsers/`
- [X] T028 [US1] Implement ParsingService and parse/block endpoints in `backend/app/services/parsing_service.py`, `backend/app/api/v1/files.py`
- [X] T029 [US1] Implement ChunkService, chunking strategy and source span writing in `backend/app/services/chunk_service.py`
- [X] T030 [US1] Implement chunk list/edit/ignore/verify endpoints in `backend/app/api/v1/chunks.py`
- [X] T031 [US1] Implement frontend file upload/list pages in `frontend/src/features/file-upload/`, `frontend/src/features/file-list/`
- [X] T032 [US1] Implement frontend chunk workspace and source locator panel in `frontend/src/features/chunk-workspace/`, `frontend/src/features/source-viewer/`

**Checkpoint**: US1 is demoable independently.

**Validation**:

```powershell
cd backend
python -m pytest tests/api/test_files_upload.py tests/service/test_file_service.py tests/unit/test_text_parser.py tests/unit/test_markdown_parser.py tests/unit/test_pdf_text_parser.py tests/unit/test_docx_text_parser.py tests/service/test_parse_service.py tests/api/test_file_parse.py tests/unit/test_chunk_strategy.py tests/service/test_chunk_service.py tests/api/test_chunks.py tests/api/test_chunk_curation.py
cd ../frontend
pnpm test -- file
pnpm test -- chunk
pnpm typecheck
```

---

## Phase 4: User Story 2 - Search and Ask with Traceable Citations (Priority: P2)

**Goal**: Search evidence and ask questions with persisted retrieval context, normalized SSE events and citations.

**Independent Test**: With seeded chunks, run keyword search, start Chat with Fake Provider, verify SSE event order and persisted citations.

### Tests for User Story 2

- [X] T033 [P] [US2] Add search service/API tests in `backend/tests/service/test_search_service.py`, `backend/tests/api/test_search.py`
- [X] T034 [P] [US2] Add Fake Provider unit tests in `backend/tests/unit/test_fake_llm_provider.py`
- [X] T035 [P] [US2] Add Chat SSE API tests in `backend/tests/api/test_chat_sse.py`
- [X] T036 [P] [US2] Add frontend search tests in `frontend/src/features/search/SearchPage.test.tsx`
- [X] T037 [P] [US2] Add frontend Chat stream tests in `frontend/src/features/chat/useChatStream.test.ts`, `frontend/src/features/chat/ChatPage.test.tsx`

### Implementation for User Story 2

- [X] T038 [US2] Create retrieval, chat and citation models plus migration in `backend/app/models/`, `backend/alembic/versions/`
- [X] T039 [US2] Implement IndexService and SearchService in `backend/app/services/index_service.py`, `backend/app/services/search_service.py`
- [X] T040 [US2] Implement search and retrieval-run inspection endpoints in `backend/app/api/v1/search.py`, `backend/app/api/router.py`
- [X] T041 [US2] Implement LLMProvider interface and FakeLLMProvider in `backend/app/providers/base.py`, `backend/app/providers/fake_llm.py`
- [X] T042 [US2] Implement ChatService and SSE endpoint in `backend/app/services/chat_service.py`, `backend/app/api/v1/chat.py`
- [X] T043 [US2] Implement frontend search page and retrieval run panel in `frontend/src/features/search/`
- [X] T044 [US2] Implement frontend Chat composer, stream hook, message list and citation panel in `frontend/src/features/chat/`
- [X] T045 [US2] Connect citations to source viewer in `frontend/src/features/source-viewer/`

**Checkpoint**: US2 is demoable independently after US1 data exists.

**Validation**:

```powershell
cd backend
python -m pytest tests/service/test_search_service.py tests/api/test_search.py tests/unit/test_fake_llm_provider.py tests/api/test_chat_sse.py
cd ../frontend
pnpm test -- search
pnpm test -- chat
pnpm typecheck
```

---

## Phase 5: User Story 3 - Turn Evidence into Maintainable Wiki Knowledge (Priority: P3)

**Goal**: Generate/edit Document Wiki, collect feedback and create evaluation sample candidates.

**Independent Test**: With seeded chunks and Fake Provider, generate Wiki draft, edit with change summary, submit feedback and convert to evaluation candidate.

### Tests for User Story 3

- [X] T046 [P] [US3] Add Wiki service/API tests in `backend/tests/service/test_wiki_service.py`, `backend/tests/api/test_wiki.py`
- [X] T047 [P] [US3] Add feedback service/API tests in `backend/tests/service/test_feedback_service.py`, `backend/tests/api/test_feedback.py`
- [X] T048 [P] [US3] Add evaluation service/API tests in `backend/tests/service/test_evaluation_service.py`, `backend/tests/api/test_evaluation_candidates.py`
- [X] T049 [P] [US3] Add Knowledge Unit and tag service/API tests in `backend/tests/service/test_knowledge_unit_service.py`, `backend/tests/api/test_knowledge_units.py`, `backend/tests/api/test_tags.py`
- [ ] T050 [P] [US3] Add frontend Knowledge Unit, tag, Wiki, feedback and evaluation tests in `frontend/src/features/knowledge-units/KnowledgeUnitPage.test.tsx`, `frontend/src/features/tags/TagManager.test.tsx`, `frontend/src/features/wiki/WikiPage.test.tsx`, `frontend/src/features/feedback/FeedbackDialog.test.tsx`, `frontend/src/features/evaluation/EvaluationCandidatePage.test.tsx`

### Implementation for User Story 3

- [X] T051 [US3] Create knowledge unit, knowledge unit source, wiki, feedback, evaluation, tag and tag binding models plus migration in `backend/app/models/`, `backend/alembic/versions/`
- [X] T052 [US3] Implement KnowledgeUnitService and knowledge unit endpoints in `backend/app/services/knowledge_unit_service.py`, `backend/app/api/v1/knowledge_units.py`
- [X] T053 [US3] Implement TagService and tag/binding endpoints in `backend/app/services/tag_service.py`, `backend/app/api/v1/tags.py`
- [X] T054 [US3] Implement WikiService and wiki endpoints in `backend/app/services/wiki_service.py`, `backend/app/api/v1/wiki.py`
- [X] T055 [US3] Implement FeedbackService and feedback endpoints including feedback-to-evaluation conversion in `backend/app/services/feedback_service.py`, `backend/app/api/v1/feedback.py`
- [X] T056 [US3] Implement EvaluationService and `/evaluation-samples` endpoints in `backend/app/services/evaluation_service.py`, `backend/app/api/v1/evaluation.py`
- [X] T057 [US3] Implement chat-message-to-evaluation endpoint in `backend/app/api/v1/chat.py`
- [ ] T058 [US3] Implement frontend Knowledge Unit and tag management pages in `frontend/src/features/knowledge-units/`, `frontend/src/features/tags/`
- [ ] T059 [US3] Implement frontend Wiki list/editor/citation panel in `frontend/src/features/wiki/`
- [ ] T060 [US3] Implement unified FeedbackDialog in `frontend/src/features/feedback/`
- [ ] T061 [US3] Implement Evaluation Candidate page in `frontend/src/features/evaluation/`

**Checkpoint**: US3 completes the LLM Wiki and feedback-to-evaluation loop.

**Validation**:

```powershell
cd backend
python -m pytest tests/service/test_knowledge_unit_service.py tests/api/test_knowledge_units.py tests/api/test_tags.py tests/service/test_wiki_service.py tests/api/test_wiki.py tests/service/test_feedback_service.py tests/api/test_feedback.py tests/service/test_evaluation_service.py tests/api/test_evaluation_candidates.py
cd ../frontend
pnpm test -- knowledge
pnpm test -- tag
pnpm test -- wiki
pnpm test -- feedback
pnpm test -- evaluation
pnpm typecheck
```

---

## Phase 6: P0 Smoke, Demo Data and Browser Validation

**Purpose**: Prove the full P0 loop is repeatable and demo-ready.

- [ ] T062 [P] Create demo data fixtures in `data/demo/company_policy.md`, `data/demo/security_handbook.pdf`, `data/demo/team_faq.docx`, `data/demo/notes.txt`
- [ ] T063 [P] Add demo data tests in `scripts/test-demo-data.ps1`, `backend/tests/service/test_seed_demo_data.py`
- [ ] T064 Implement demo seed script in `scripts/seed-demo-data.ps1`
- [ ] T065 Implement P0 smoke script in `scripts/smoke-p0.ps1`
- [ ] T066 [P] Add Playwright config and P0 browser smoke in `frontend/playwright.config.ts`, `frontend/e2e/p0-smoke.spec.ts`
- [ ] T067 Update README with Spec Kit workflow, local startup and smoke commands in `README.md`
- [ ] T068 Run quickstart validation from `specs/001-knowweave-p0/quickstart.md`

**Validation**:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test-demo-data.ps1
powershell -ExecutionPolicy Bypass -File scripts/seed-demo-data.ps1
powershell -ExecutionPolicy Bypass -File scripts/smoke-p0.ps1
cd frontend
pnpm test:e2e
```

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; T001-T007 already complete in current working tree.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories. T008-T009 already complete in current working tree.
- **US1 (Phase 3)**: Depends on all foundational tasks.
- **US2 (Phase 4)**: Depends on foundational tasks and benefits from US1 seeded chunks.
- **US3 (Phase 5)**: Depends on US1 evidence and US2 retrieval/chat entities.
- **Smoke (Phase 6)**: Depends on selected P0 stories being complete.

### User Story Dependencies

- **US1**: Can be implemented first and independently demonstrates upload-to-evidence governance.
- **US2**: Requires searchable evidence, so it should follow US1 data model/service readiness.
- **US3**: Requires evidence and citations; implement after US1 and US2 backend foundations.

### Parallel Opportunities

- Tests for each story marked `[P]` can be written in parallel.
- Frontend tests can proceed with MSW mocks while backend services are under development.
- Model files serving different domains can be created in parallel, but migrations must be serialized.
- Demo data and browser smoke scaffolding can start after frontend/backend routes are stable.

## Implementation Strategy

### MVP First

1. Finish Phase 2 foundational tasks.
2. Complete US1 upload/parse/chunk/source-span governance.
3. Validate US1 independently.
4. Add US2 search/chat/citation.
5. Add US3 Wiki/feedback/evaluation.
6. Finish smoke and browser validation.

### TDD Rule

For each story phase, write the test tasks first and confirm they fail for the expected missing behavior before implementing the corresponding service/API/UI tasks.

### Completion Rule

Mark each task `[X]` only after its validation command passes or the reason for a skipped validation is recorded in the final development note.
