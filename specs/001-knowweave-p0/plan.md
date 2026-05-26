# Implementation Plan: KnowWeave P0 Knowledge Workbench

**Branch**: `001-knowweave-p0` | **Date**: 2026-05-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-knowweave-p0/spec.md`

## Summary

Build KnowWeave P0 as a local-first, evidence-governed LLM Wiki knowledge workbench. The implementation delivers upload, parse, chunk/source-span governance, keyword search, traceable Chat SSE, Document Wiki, feedback and evaluation candidate loops. The technical approach follows the detailed repository specs under `docs/`, using a FastAPI backend, PostgreSQL/pgvector, SQLAlchemy/Alembic, a Next.js frontend, Fake Provider test paths and PowerShell smoke scripts.

## Technical Context

**Language/Version**: Python 3.11+ for backend; TypeScript for frontend.

**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, httpx, pytest, Next.js App Router, React, Tailwind CSS, Vitest, Testing Library, MSW, Playwright.

**Storage**: PostgreSQL 15+ with pgvector and pg_trgm extensions; local filesystem for uploaded files; local demo data under `data/demo/`.

**Testing**: pytest and pytest-asyncio for backend unit/service/API/database tests; Vitest and Testing Library for frontend unit/component tests; Playwright and PowerShell smoke scripts for P0 browser/API flows.

**Target Platform**: Local Windows PowerShell development first; local Docker Compose for Postgres and P0 demo; Linux-compatible containers later.

**Project Type**: Web application with separated backend API, frontend UI, database and local scripts.

**Performance Goals**: P0 supports 20-100 demo files, files up to 20 MB, up to 500 chunks per file, up to 2000 knowledge units and demo Chat response completion within 30 seconds with Fake Provider or available model.

**Constraints**: No real API keys in source control; no uploaded runtime data committed; tests must not depend on real Qwen; AI outputs and citations must remain source-traceable; ignored/archived/soft-deleted evidence must be excluded from default retrieval.

**Scale/Scope**: P0 covers one local knowledge workspace and does not include full permissions, multi-tenancy, production deployment, complex vector quality tuning, distributed queues or deep multimodal parsing.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The ratified KnowWeave constitution in `.specify/memory/constitution.md` applies to this feature:

- TDD is required for business tasks: write tests before or with implementation and record commands.
- Every task needs at least one automated verification entry.
- Provider, parsing, SSE, feedback and evaluation candidate paths must have fake/mock support.
- Database tasks must cover migration or test database initialization.
- Runtime secrets, uploaded files and logs must not be committed.
- Implementation must remain traceable to `docs/01-product-spec.md` through `docs/14-tdd-task-breakdown.md`.

Gate result: PASS. No justified complexity violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-knowweave-p0/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi-p0.yaml
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── providers/
│   ├── schemas/
│   └── services/
├── alembic/
└── tests/
    ├── api/
    ├── db/
    ├── service/
    └── unit/

frontend/
├── src/
│   ├── app/
│   ├── app-shell/
│   ├── features/
│   └── shared/
└── e2e/

docker/
└── postgres/

data/
├── demo/
└── files/

scripts/
```

**Structure Decision**: Use a web application layout with separate `backend/` and `frontend/`, plus root-level `docker/`, `data/`, `scripts/`, `docs/` and `specs/`. Backend owns API, services, providers, persistence and smoke-compatible endpoints. Frontend owns the evidence-first workbench UI, API client and browser tests.

## Complexity Tracking

No constitution violations identified.
