# KnowWeave

![KnowWeave Logo](docs/assets/knowweave-logo.png)

面向企业知识文件的 LLM Wiki 知识库管理平台。

KnowWeave 关注的不只是“上传文件后问答”，而是把知识文件经过上传、解析、分块、检索、沉淀、反馈和评估，逐步治理成可追溯、可编辑、可演化的组织知识资产。

## 当前阶段

项目当前处于 P0 收口阶段。Spec Kit P0 任务已完成工程骨架、上传解析、chunk 治理、搜索问答、Wiki、feedback、evaluation candidate、demo 数据、后端 smoke 和前端浏览器 smoke；剩余收口项以 `specs/001-knowweave-p0/tasks.md` 为准。

工程推进规则：

- 先读 `specs/001-knowweave-p0/tasks.md`，只领取未完成任务。
- 每个任务遵循 `docs/14-tdd-task-breakdown.md` 的 Red / Green / Refactor 节奏。
- 每个小任务完成后单独提交，提交信息使用 Conventional Commits。
- 任务完成后再把 `tasks.md` 中对应项标记为 `[X]`，并单独提交。

## 核心方向

- LLM Wiki：将文件、chunk、Knowledge Unit、问答反馈沉淀为可维护 Wiki 页面。
- 细粒度知识治理：支持人工查看、编辑、忽略、确认 chunk 和 Knowledge Unit。
- 可追溯引用：回答、Wiki 和知识单元都应能回到原始文件位置。
- 闭环评估：沉淀用户问题、召回上下文、回答、引用和反馈，用于构建评测样本。
- 可扩展解析：MVP 先支持文本主链路，后续扩展表格、图片、公式、代码和音视频。

## 文档入口

阅读顺序见 [docs/README.md](docs/README.md)。

当前已完成的主要文档：

1. [项目可视化驾驶舱](docs/00-project-dashboard.md)
2. [产品需求规格](docs/01-product-spec.md)
3. [知识生命周期规格](docs/02-knowledge-lifecycle-spec.md)
4. [系统架构规格](docs/03-system-architecture-spec.md)
5. [数据模型规格](docs/04-data-model-spec.md)
6. [Ingestion 规格](docs/05-ingestion-spec.md)
7. [LLM Wiki 规格](docs/06-llm-wiki-spec.md)
8. [搜索与问答规格](docs/07-search-and-chat-spec.md)
9. [前端交互规格](docs/08-frontend-spec.md)
10. [验收测试规格](docs/09-acceptance-test-spec.md)
11. [评测与反馈闭环规格](docs/10-evaluation-spec.md)
12. [后端实现规格](docs/11-backend-implementation-spec.md)
13. [前端实现规格](docs/12-frontend-implementation-spec.md)
14. [DevOps 与 Demo 规格](docs/13-devops-and-demo-spec.md)
15. [TDD 任务拆解说明书](docs/14-tdd-task-breakdown.md)

## Spec Kit 工作流

P0 的权威任务入口：

- [P0 spec](specs/001-knowweave-p0/spec.md)
- [P0 plan](specs/001-knowweave-p0/plan.md)
- [P0 tasks](specs/001-knowweave-p0/tasks.md)
- [P0 quickstart](specs/001-knowweave-p0/quickstart.md)
- [P0 OpenAPI contract](specs/001-knowweave-p0/contracts/openapi-p0.yaml)

推荐执行顺序：

```powershell
git status --short
Get-Content specs\001-knowweave-p0\tasks.md
```

选择下一个未完成任务后：

1. 先补或确认对应测试。
2. 实现最小可验证行为。
3. 运行任务对应验证命令。
4. 用 Conventional Commit 提交任务实现。
5. 标记 `tasks.md` 对应任务为 `[X]`，再单独提交任务清单更新。

## 本地启动

### 1. 数据库

```powershell
docker compose up -d postgres
powershell -ExecutionPolicy Bypass -File scripts/test-compose.ps1
```

### 2. 后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
alembic upgrade head
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

也可以从仓库根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev-backend.ps1
```

健康检查：

```powershell
Invoke-WebRequest http://localhost:8000/api/v1/health -UseBasicParsing
```

### 3. 前端

```powershell
cd frontend
pnpm install
pnpm dev
```

也可以从仓库根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev-frontend.ps1
```

默认打开 `http://localhost:3000`。Playwright browser smoke 会使用独立端口 `http://127.0.0.1:4317`，避免复用本机已有的 3000 端口服务。

## 验证命令

后端：

```powershell
cd backend
python -m pytest
```

前端：

```powershell
cd frontend
pnpm test
pnpm typecheck
pnpm test:e2e
```

首次运行 Playwright 时如提示缺少浏览器，先执行：

```powershell
cd frontend
pnpm exec playwright install chromium
```

Demo 数据与 smoke：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test-demo-data.ps1
powershell -ExecutionPolicy Bypass -File scripts/seed-demo-data.ps1
powershell -ExecutionPolicy Bypass -File scripts/smoke-health.ps1
powershell -ExecutionPolicy Bypass -File scripts/smoke-p0.ps1
```

`scripts/smoke-p0.ps1` 需要 PostgreSQL、后端 API 和 migration 可用；输出中应包含 `backend_health`、`migration_ok`、`file_id`、`chunk_count`、`retrieval_run_id`、`chat_message_id`、`feedback_id`、`evaluation_sample_id` 和 `result`。

## MVP 边界

MVP 优先完成：

- txt、md、pdf、docx 文件上传与基础解析。
- Document Block、text chunk、source span。
- chunk 查看、编辑、忽略、确认和原文定位。
- Knowledge Unit 管理。
- Document Wiki 生成。
- 关键词搜索、AI 问答、citation、问答记录和 retrieved_contexts。

P1/P2 再逐步扩展向量检索、模型配置页面、Wiki Revision 对比回滚、表格/图片/公式/代码深度解析和音视频解析。
