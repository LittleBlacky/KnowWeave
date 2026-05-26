# KnowWeave Constitution

## Core Principles

### I. Evidence-First Knowledge

Every AI-generated answer, Wiki claim, Knowledge Unit and evaluation sample must remain traceable to original files, chunks, source spans or explicit manual sources. Unsupported claims are not accepted as trusted knowledge.

### II. Human-Governed AI Output

AI output starts as draft or pending review. Users must be able to inspect, edit, ignore, verify, archive and provide feedback on generated chunks, Knowledge Units, Wiki pages, citations and answers.

### III. Test-First Implementation

P0 engineering follows Red / Green / Refactor. Business tasks require tests before or alongside implementation, and each completed task must record the actual verification command and result.

### IV. Deterministic Provider Boundary

External model providers must be hidden behind provider interfaces. Provider, parsing, Chat SSE, Wiki generation, feedback and evaluation flows must have fake or mock paths so tests and demos do not require real API keys.

### V. Local-First, Recoverable P0

P0 must run locally with documented commands, Docker Compose for PostgreSQL, local file storage and smoke scripts. Failures in parsing, migration, provider calls or streaming must leave inspectable state and a retry/debug path.

## Engineering Constraints

- Backend code uses FastAPI, Pydantic, SQLAlchemy and Alembic unless a future plan explicitly supersedes this.
- Frontend code uses Next.js, TypeScript and an evidence-first workbench UI unless a future plan explicitly supersedes this.
- PostgreSQL with pgvector and pg_trgm is the target database baseline; semantic vector retrieval quality tuning is not part of P0.
- Runtime secrets, `.env`, uploaded files, local databases and logs must not be committed.
- API contracts, data models and UI flows must remain traceable to `specs/001-knowweave-p0/` and the detailed references under `docs/`.

## Development Workflow

- Start from Spec Kit artifacts in `specs/001-knowweave-p0/`.
- Implement tasks from `tasks.md` in order, respecting phase dependencies and `[P]` parallel markers.
- Mark each completed task as `[X]` in `tasks.md`.
- Run the validation command attached to the affected task or phase before marking it complete.
- Prefer Fake Provider paths for automated tests; real provider checks are optional integration checks gated by explicit credentials.

## Governance

This constitution supersedes ad hoc implementation habits for KnowWeave P0. Changes to core scope, provider behavior, source traceability, task ordering or testing rules require updating the relevant Spec Kit artifact first, then code.

**Version**: 1.0.0 | **Ratified**: 2026-05-26 | **Last Amended**: 2026-05-26
