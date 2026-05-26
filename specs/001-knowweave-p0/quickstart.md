# Quickstart: KnowWeave P0

## Prerequisites

- Python 3.11+
- Node.js and pnpm
- Docker with Compose
- PowerShell on Windows

## 1. Start Database

```powershell
docker compose up -d postgres
powershell -ExecutionPolicy Bypass -File scripts/test-compose.ps1
```

## 2. Install and Test Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
alembic upgrade head
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```powershell
Invoke-WebRequest http://localhost:8000/api/v1/health -UseBasicParsing
```

## 3. Start Frontend

```powershell
cd frontend
pnpm install
pnpm test
pnpm typecheck
pnpm dev
```

Open `http://localhost:3000`.

## 4. Run P0 Smoke

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke-p0.ps1
```

Expected output includes:

- backend_health
- migration_ok
- file_id
- chunk_count
- retrieval_run_id
- chat_message_id
- feedback_id
- evaluation_sample_id
- result

## 5. Demo Flow

1. Upload demo Markdown.
2. Parse the file.
3. Build and review chunks.
4. Verify or ignore at least one chunk.
5. Create or edit a Knowledge Unit and bind a tag.
6. Run keyword search.
7. Ask a Chat question and inspect citations.
8. Generate Document Wiki.
9. Submit feedback.
10. Create evaluation sample candidate.

## 6. Fallback Rules

- If Qwen is unavailable, use Fake Provider.
- If PDF/DOCX parsing is unstable, run the Markdown main path first and keep PDF/DOCX as explicit degraded checks.
- If frontend is unavailable, run API smoke and show OpenAPI/backend logs.
