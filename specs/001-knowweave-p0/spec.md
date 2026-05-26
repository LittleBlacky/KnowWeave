# Feature Specification: KnowWeave P0 Knowledge Workbench

**Feature Branch**: `001-knowweave-p0`

**Created**: 2026-05-26

**Status**: Draft

**Input**: User description: "根据 KnowWeave/docs 底下的 spec 补充完 spec-kit 需要的规范"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Govern Uploaded Knowledge Evidence (Priority: P1)

知识管理员上传企业知识文件后，需要看到文件记录、解析状态、document blocks、chunks 和 source spans，并能对 chunk 进行查看、编辑、忽略和确认。

**Why this priority**: 这是 KnowWeave 的事实源入口。没有可追踪的文件、chunk 和 source span，后续 Wiki、Search、Chat、Feedback 都无法证明答案来源。

**Independent Test**: 上传 Markdown 或 txt 文件后，系统保存文件元数据，解析出 blocks/chunks/source spans，并允许用户编辑、ignore、verify chunk；该流程不依赖真实 LLM Provider。

**Acceptance Scenarios**:

1. **Given** 一个空知识库，**When** 用户上传支持的 Markdown 文件，**Then** 文件列表展示文件名、类型、大小、状态和上传时间。
2. **Given** 文件已上传，**When** 用户触发解析，**Then** 系统生成 parse result、document blocks、chunks 和可定位到原文的 source spans。
3. **Given** chunk 已生成，**When** 用户编辑 chunk 内容，**Then** 系统保存 edited content 且不覆盖 raw content。
4. **Given** chunk 被标记为 ignored，**When** 用户执行默认搜索或问答，**Then** 该 chunk 不进入默认召回候选。

---

### User Story 2 - Search and Ask with Traceable Citations (Priority: P2)

知识消费者需要通过关键词搜索和 AI 问答获取知识，并能看到每个结果、回答和 citation 的来源证据。

**Why this priority**: KnowWeave 不只是文件管理工具，必须证明搜索、RAG、引用和 retrieved contexts 是可回放、可评估的。

**Independent Test**: 在已存在 chunks 的情况下，用户执行搜索和 Chat，系统返回 retrieval_run_id、可解释结果、SSE 回答事件和 citations，并保存问答记录。

**Acceptance Scenarios**:

1. **Given** 已解析并生成 searchable chunks，**When** 用户输入关键词，**Then** 搜索结果展示类型、标题、摘要、score 和 source locator。
2. **Given** 存在可召回上下文，**When** 用户发起 Chat，**Then** 系统按 start、retrieval、delta、citations、done 顺序返回 SSE 事件。
3. **Given** 回答完成，**When** 用户查看回答，**Then** 回答包含 citation 且 citation 可回溯到 chunk 或 source span。
4. **Given** 用户问题没有可用依据，**When** 系统生成回答，**Then** 系统明确说明无法基于现有知识回答，不编造来源。

---

### User Story 3 - Turn Evidence into Maintainable Wiki Knowledge (Priority: P3)

知识管理员和领域专家需要把文件、chunk 和问答沉淀为可编辑 Document Wiki，并通过反馈形成 evaluation sample candidate。

**Why this priority**: LLM Wiki 是 KnowWeave 与普通 RAG 的核心差异。Wiki 和 Feedback 让临时问答变成长期可维护知识资产和评测闭环。

**Independent Test**: 在已存在文件和 chunks 的情况下，用户创建或编辑 Knowledge Unit、维护标签，系统用 Fake Provider 生成 Document Wiki draft，用户编辑 Wiki 并提交 change summary，再提交 feedback 并生成 evaluation candidate。

**Acceptance Scenarios**:

1. **Given** 文件已有 chunks，**When** 用户生成 Document Wiki，**Then** 系统创建 draft Wiki，内容包含 citations 或 source links。
2. **Given** Wiki 已生成，**When** 用户编辑 Wiki，**Then** 用户必须填写 change summary，系统保存新内容和状态。
3. **Given** chunk 或人工知识来源存在，**When** 用户创建或编辑 Knowledge Unit，**Then** 系统保存标题、正文、类型、状态、标签和来源关系。
4. **Given** 标签已创建，**When** 用户绑定标签到文件、Knowledge Unit 或 Wiki，**Then** 列表筛选和详情页展示该标签。
5. **Given** 用户对 answer、citation、chunk 或 wiki 提交反馈，**When** feedback 保存成功，**Then** feedback 关联目标对象并可转为 evaluation sample candidate。
6. **Given** evaluation candidate 已生成，**When** 用户查看评测列表，**Then** 系统展示 question、answer、来源快照和候选状态。

---

### Edge Cases

- Unsupported file type uploads return a clear validation error and do not create active file records.
- Parser failures preserve the original file and record parse failure status plus readable error details.
- Soft-deleted files keep historical Wiki, Chat, Citation and Evaluation records, but related chunks are excluded from default retrieval.
- Source files unavailable or deleted must be visible in citation/source viewer state instead of silently hiding references.
- Fake Provider must support deterministic Wiki and Chat tests when real Qwen API is unavailable.
- SSE interruptions must leave persisted messages in completed, failed, or partial state with enough metadata to debug.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support upload and listing for txt, md, pdf and docx knowledge files in P0.
- **FR-002**: System MUST preserve original file metadata including filename, type, size, sha256, storage path, status and timestamps.
- **FR-003**: System MUST parse supported files into parse results and document blocks with status and error tracking.
- **FR-004**: System MUST generate chunks from document blocks and record source spans that allow source viewer navigation or source locator display.
- **FR-005**: Users MUST be able to view, edit, ignore and verify chunks without overwriting raw chunk content.
- **FR-006**: System MUST exclude ignored, archived and soft-deleted-source chunks from default search and Chat retrieval.
- **FR-007**: System MUST provide keyword search over files, chunks, knowledge units and wiki pages, returning typed results with retrieval_run_id.
- **FR-008**: System MUST persist retrieved contexts for Search and Chat so retrieval can be inspected after the response.
- **FR-009**: System MUST provide Chat with normalized SSE events: start, retrieval, delta, citations, done and error.
- **FR-010**: System MUST save chat sessions, user messages, assistant answers, citations and provider metadata after Chat completion or failure.
- **FR-011**: System MUST provide a Fake LLM Provider for deterministic tests and demos without real external model calls.
- **FR-012**: System MUST generate Document Wiki drafts from files/chunks and save source citations.
- **FR-013**: Users MUST be able to edit Wiki content and status; Wiki edits MUST include change_summary.
- **FR-014**: Users MUST be able to create, view, edit, filter and update status for Knowledge Units.
- **FR-015**: Users MUST be able to create tags, bind tags to files, Knowledge Units and Wiki pages, and filter by tags.
- **FR-016**: System MUST support unified feedback for chat messages, citations, retrieved contexts, chunks and wiki pages.
- **FR-017**: System MUST create evaluation sample candidates from feedback or chat records while preserving retrieved context and citation snapshots.
- **FR-018**: System MUST provide local development scripts, env examples, Postgres/pgvector initialization and P0 smoke checks.
- **FR-019**: System MUST keep API keys and uploaded runtime data out of source control.
- **FR-020**: System MUST keep detailed implementation requirements traceable to `docs/01-product-spec.md` through `docs/14-tdd-task-breakdown.md`.

### Key Entities *(include if feature involves data)*

- **KnowledgeFile**: Original uploaded file and immutable fact source metadata.
- **ParseResult**: One parse run for a file, including parser status, raw text, warnings and errors.
- **DocumentBlock**: Structured block extracted from a file, such as heading, paragraph, table, code or placeholder.
- **Chunk**: Governable evidence unit used for retrieval, citations, Wiki and knowledge curation.
- **SourceSpan**: Locator that ties a chunk or citation back to file position, page, line, character range, bbox or timeline.
- **KnowledgeUnit**: Fine-grained curated knowledge object that can be draft, pending_review, verified or archived.
- **WikiPage**: Long-lived LLM Wiki page with Markdown content, curation status, source file and citations.
- **Citation**: Relationship between generated/curated content and the supporting source evidence.
- **ChatSession / ChatMessage**: User and assistant conversation records with final answer state.
- **RetrievedContext**: Search or Chat retrieval result grouped by retrieval_run_id.
- **Feedback**: User feedback tied to answer, citation, retrieval context, chunk or wiki.
- **EvaluationSample**: Candidate or verified evaluation item derived from feedback, chat or manual curation.
- **Tag / TagBinding**: Lightweight organization metadata for files, knowledge units and wiki pages.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time developer can start the P0 database and backend health path from the documented commands in under 10 minutes on a prepared machine.
- **SC-002**: The P0 smoke script reports backend_health, migration_ok, file_id, chunk_count, retrieval_run_id, chat_message_id, feedback_id, evaluation_sample_id and final result.
- **SC-003**: At least one Markdown demo file can complete upload, parse, chunk build, search, Chat, feedback and evaluation candidate creation in a repeatable smoke run.
- **SC-004**: 100% of Chat answers generated in the P0 happy path include at least one citation or an explicit no-evidence response.
- **SC-005**: 100% of Wiki edits require and persist a change summary.
- **SC-006**: All P0 tasks include an automated verification command and can be mapped back to a user story or foundational phase.
- **SC-007**: The system can run unit/API tests for backend core paths without a real Qwen API key.
- **SC-008**: No committed file contains real API keys, uploaded private files or local runtime logs.

## Assumptions

- P0 is single-user or local-user mode; enterprise permissions and multi-tenancy are out of scope.
- P0 defaults to local or single-machine deployment.
- PostgreSQL 15 with pgvector is the target database baseline; tests may use temporary SQLite only for infrastructure-level migration/session checks where appropriate.
- Qwen/OpenAI-compatible models are the default real LLM path, but Fake Provider is mandatory for tests and demos.
- MVP primarily supports text-first processing; rich table, image, formula, code and audio/video parsing are later expansions.
- Vector search is installed/prepared through pgvector but semantic retrieval quality tuning is P1.
- Existing `docs/` files remain authoritative deep references; this Spec Kit feature is the executable summary and implementation control surface.
