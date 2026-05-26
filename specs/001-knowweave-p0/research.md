# Research: KnowWeave P0 Knowledge Workbench

## Decision: Use FastAPI service-layer backend

**Rationale**: Existing specs require clear API, Service, Repository and Provider boundaries, SSE support, file upload, testability and Python parser ecosystem compatibility.

**Alternatives considered**: Flask was simpler but weaker for typed API contracts. Django was heavier than P0 needs. Node backend would duplicate frontend language but weakens Python parsing/provider fit.

## Decision: Use PostgreSQL 15 with pgvector installed, keyword retrieval first

**Rationale**: Core entities are relational and need source traceability, status filtering, citations, feedback and evaluation snapshots. pgvector is installed as a baseline but P0 avoids semantic quality tuning risk by using keyword/full-text retrieval first.

**Alternatives considered**: SQLite is useful for limited tests but not the target data store. Vector-only stores make source governance, revisions and feedback relationships harder.

## Decision: Use local filesystem storage in P0

**Rationale**: P0 is local-first and demo-oriented. Local storage makes upload, source viewer and smoke tests straightforward while preserving a future StorageProvider boundary.

**Alternatives considered**: S3/MinIO would improve production parity but adds deployment and credential complexity outside P0.

## Decision: Use Fake LLM Provider as mandatory implementation path

**Rationale**: Tests, demos and CI must not depend on real Qwen availability. Fake Provider enables deterministic Chat SSE, Wiki generation, feedback and evaluation candidate tests.

**Alternatives considered**: Calling real Qwen in all tests would be flaky, costly and impossible without secrets. Static pre-generated responses alone would not validate provider abstraction.

## Decision: Use SSE for Chat streaming

**Rationale**: Chat output is server-to-client streaming, so SSE is adequate and simpler than WebSocket. Existing specs define start, retrieval, delta, citations, done and error events.

**Alternatives considered**: WebSocket is reserved for P1/P2 task status push and bidirectional long-running jobs.

## Decision: Use Next.js App Router with a three-pane evidence workbench

**Rationale**: Existing UI specs and prototype work converge on left navigation, central workspace and persistent right evidence inspector for chunks, citations and source viewer.

**Alternatives considered**: A simple upload-and-chat layout would not express KnowWeave's governance-heavy differentiation.

## Decision: Implement in TDD task slices

**Rationale**: `docs/14-tdd-task-breakdown.md` already defines Sprint 0 through Sprint 5 with Red/Green/Refactor expectations and validation commands. Spec Kit tasks should preserve that ordering.

**Alternatives considered**: Building feature-by-feature without tests risks losing source-traceability and feedback/evaluation guarantees.
