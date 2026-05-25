# KnowWeave DevOps 与 Demo 规格说明书

版本：v0.1
日期：2026-05-25
状态：草案
关联文档：`docs/09-acceptance-test-spec.md`、`docs/11-backend-implementation-spec.md`、`docs/12-frontend-implementation-spec.md`

## 0. 文档边界

本文定义 KnowWeave P0 如何在本地和单机环境中稳定启动、演示和验收，包括：

- Docker Compose 服务编排。
- PostgreSQL + pgvector 初始化。
- 后端、前端、数据库、文件存储的环境变量。
- 本地开发启动命令。
- 演示数据目录、seed 脚本和 P0 smoke 脚本。
- 答辩演示流程、检查清单和故障预案。

本文不负责：

- 云上生产部署、Kubernetes、CI/CD、灰度发布和多环境密钥管理。
- 企业级对象存储、权限系统、审计系统和多租户隔离。
- 完整性能压测和安全渗透测试。

## 1. 实现目标

第 13 篇的目标是让 KnowWeave 从规格文档进入可运行工程骨架。

P0 DevOps 必须做到：

- 新成员可以在本地通过少量命令启动数据库、后端和前端。
- 空数据库可以自动安装 pgvector 并执行 Alembic migration。
- 演示数据可以一键导入或按脚本上传。
- P0 smoke 可以验证上传、解析、chunk、search、chat、feedback 和 evaluation candidate 主链路。
- 答辩时出现 Provider、网络或解析失败时，有明确降级方案。

## 2. P0 部署形态

P0 只要求本地或单机部署。

| 环境 | 用途 | 必须支持 | 说明 |
| --- | --- | --- | --- |
| Local Dev | 日常开发 | 是 | 后端和前端可用本机命令启动，数据库用 Compose |
| Local Compose | 一键演示 | 是 | PostgreSQL、backend、frontend 全部由 Compose 启动 |
| CI Smoke | 基础回归 | P1 | 后续接入 GitHub Actions 或本地脚本 |
| Production | 生产部署 | 否 | P0 不覆盖 |

推荐优先级：

1. 先保证 Local Dev。
2. 再保证 Local Compose。
3. 最后补 CI Smoke。

## 3. 服务拓扑

```mermaid
flowchart LR
  Browser["Browser"] --> Frontend["Next.js frontend"]
  Frontend --> Backend["FastAPI backend"]
  Backend --> Postgres["PostgreSQL + pgvector"]
  Backend --> Storage["Local file storage"]
  Backend --> Qwen["Qwen Provider"]
  Backend --> Logs["Local logs"]
  Smoke["Smoke scripts"] --> Backend
  Smoke --> Frontend
```

P0 服务：

| 服务 | 端口 | 说明 |
| --- | --- | --- |
| `postgres` | `5432` | PostgreSQL 15+，安装 pgvector |
| `backend` | `8000` | FastAPI API，路径前缀 `/api/v1` |
| `frontend` | `3000` | Next.js 前端 |

P0 不引入：

- Redis。
- Celery / RQ。
- Nginx。
- MinIO。
- OpenTelemetry Collector。

这些可以在 P1/P2 增加。

## 4. 目录结构

建议工程根目录：

```text
KnowWeave/
  backend/
  frontend/
  docker/
    postgres/
      init.sql
  data/
    files/
    demo/
      company_policy.md
      security_handbook.pdf
      team_faq.docx
      notes.txt
  scripts/
    dev-backend.ps1
    dev-frontend.ps1
    smoke-p0.ps1
    seed-demo-data.ps1
  docs/
  docker-compose.yml
  .env.example
  README.md
```

目录规则：

- `data/files/` 是本地上传文件存储根目录，默认不提交上传产物。
- `data/demo/` 存放可提交的演示样例文件。
- `scripts/` 存放跨平台启动和 smoke 脚本；P0 优先支持 Windows PowerShell。
- `.env.example` 必须包含全部变量和注释，不包含真实密钥。

## 5. Docker Compose

### 5.1 Compose 服务

P0 `docker-compose.yml` 必须包含：

| 服务 | image / build | 依赖 | 健康检查 |
| --- | --- | --- | --- |
| `postgres` | `pgvector/pgvector:pg15` 或自定义 postgres + vector | 无 | `pg_isready` |
| `backend` | `./backend` | postgres | `/api/v1/health` |
| `frontend` | `./frontend` | backend | `/` |

Compose 规则：

- 数据库使用 named volume。
- 后端挂载 `./data/files:/app/data/files`。
- 前端通过 `NEXT_PUBLIC_API_BASE_URL` 指向后端。
- 后端等待数据库健康后再启动。

### 5.2 最小 Compose 示例

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: knowweave
      POSTGRES_USER: knowweave
      POSTGRES_PASSWORD: knowweave
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U knowweave -d knowweave"]
      interval: 5s
      timeout: 3s
      retries: 20

  backend:
    build:
      context: ./backend
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql+psycopg://knowweave:knowweave@postgres:5432/knowweave
      FILE_STORAGE_ROOT: /app/data/files
    ports:
      - "8000:8000"
    volumes:
      - ./data/files:/app/data/files
    depends_on:
      postgres:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
    environment:
      NEXT_PUBLIC_API_BASE_URL: http://localhost:8000/api/v1
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

## 6. 数据库初始化

`docker/postgres/init.sql`：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

启动后端时必须执行：

```text
alembic upgrade head
```

P0 可以先在 backend entrypoint 中执行 migration，但必须满足：

- migration 失败时后端启动失败。
- migration 日志可见。
- 重复执行必须幂等。

P1 再拆分为独立 migration job。

## 7. 环境变量

### 7.1 根 `.env.example`

```env
APP_ENV=development
DATABASE_URL=postgresql+psycopg://knowweave:knowweave@localhost:5432/knowweave
FILE_STORAGE_ROOT=./data/files
MAX_UPLOAD_MB=50
ENABLE_PGVECTOR=true

QWEN_API_KEY=
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_CHAT_MODEL=qwen-plus
QWEN_GENERATION_MODEL=qwen-plus
QWEN_TIMEOUT_SECONDS=60

NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_ENV=development
NEXT_PUBLIC_ENABLE_MOCKS=false
```

### 7.2 密钥规则

- `.env` 不提交。
- `.env.example` 必须提交。
- `QWEN_API_KEY` 只在后端读取。
- 前端不得使用任何 Provider API Key。
- 演示时如果不使用真实 Qwen，必须切换到 Fake Provider。

## 8. 本地开发命令

### 8.1 数据库

```powershell
docker compose up -d postgres
```

### 8.2 后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 8.3 前端

```powershell
cd frontend
npm install
npm run dev
```

### 8.4 一键演示

```powershell
docker compose up --build
```

访问：

| 服务 | URL |
| --- | --- |
| Frontend | `http://localhost:3000` |
| Backend Health | `http://localhost:8000/api/v1/health` |
| OpenAPI | `http://localhost:8000/docs` |

## 9. 演示数据

演示数据目录：

```text
data/demo/
  company_policy.md
  security_handbook.pdf
  team_faq.docx
  notes.txt
```

数据要求：

| 文件 | 用途 |
| --- | --- |
| `company_policy.md` | Markdown 解析、chunk、Wiki 和行号定位 |
| `security_handbook.pdf` | PDF 页码定位和 citation |
| `team_faq.docx` | DOCX block 和 FAQ 类问答 |
| `notes.txt` | 纯文本基础链路 |

P0 seed 脚本可以有两种模式：

- API 模式：调用上传 API 导入文件。
- 文件模式：只把样例文件复制到 `data/demo/`，由演示者手动上传。

优先实现 API 模式，文件模式作为降级方案。

## 10. P0 Smoke

Smoke 脚本目标是快速判断主链路是否能跑。

推荐脚本：

```text
scripts/smoke-p0.ps1
```

检查步骤：

```mermaid
flowchart TD
  Health["Check backend health"] --> Upload["Upload demo markdown"]
  Upload --> Parse["Trigger parse"]
  Parse --> Chunks["Assert chunks exist"]
  Chunks --> Search["Run keyword search"]
  Search --> Chat["Send chat question"]
  Chat --> Feedback["Submit feedback"]
  Feedback --> Eval["Create evaluation candidate"]
```

Smoke 必须输出：

| 字段 | 说明 |
| --- | --- |
| backend_health | 后端是否可用 |
| migration_ok | migration 是否已执行 |
| file_id | 上传文件 ID |
| chunk_count | chunk 数量 |
| retrieval_run_id | 搜索运行 ID |
| chat_message_id | Chat 消息 ID |
| feedback_id | 反馈 ID |
| evaluation_sample_id | 样本 ID |
| result | pass / fail |

P0 smoke 不验证答案质量，只验证链路可用和数据可追踪。

## 11. 答辩演示流程

演示总时长建议 8 到 12 分钟。

| 阶段 | 时长 | 内容 |
| --- | --- | --- |
| 项目定位 | 1 分钟 | 说明 KnowWeave 不只是 RAG，而是治理型 LLM Wiki |
| 文件导入 | 2 分钟 | 上传 Markdown / PDF，展示 parse、blocks、chunks |
| Chunk 治理 | 2 分钟 | 编辑、ignore、verify、Source Viewer |
| Search / Chat | 2 分钟 | 搜索、提问、SSE、citation |
| Wiki 沉淀 | 2 分钟 | 生成 Wiki、查看引用、编辑 change_summary |
| Feedback / Evaluation | 1 分钟 | citation_wrong、转 evaluation candidate |
| 工程闭环 | 1 分钟 | 展示 Docker、Smoke、日志和后续 P1 |

演示叙事：

1. 文件进入系统不是黑盒，用户能看到 parse 和 chunk。
2. chunk 可以被治理，来源可以被追踪。
3. Search 和 Chat 不是临时答案，召回和引用会沉淀。
4. Wiki 是长期知识资产。
5. Feedback 进入评测样本，形成持续改进闭环。

## 12. 故障预案

| 故障 | 演示影响 | 降级方案 |
| --- | --- | --- |
| Qwen API 不可用 | Chat / Wiki 生成失败 | 切 Fake Provider，展示固定流式输出 |
| 网络不稳定 | Provider 超时 | 预置已有 chat message 和 wiki draft |
| PDF 解析失败 | PDF 演示受影响 | 切 Markdown 主链路，PDF 作为失败重试展示 |
| 数据库未启动 | 全链路不可用 | 先展示 docs 和架构，后台启动 Compose |
| 前端 build 失败 | UI 不可用 | 使用 dev server 或截图作为临时说明 |
| Mermaid / 飞书画板失败 | 文档展示受影响 | 使用本地 Markdown 作为事实源 |

P0 必须准备：

- Fake Provider。
- 预置 demo 数据。
- 一份已生成的 Wiki draft。
- 一次已完成的 Chat 记录。
- smoke 输出截图或日志。

## 13. 日志与排错

P0 日志位置：

| 对象 | 位置 |
| --- | --- |
| backend logs | stdout / `logs/backend.log` |
| frontend logs | stdout |
| postgres logs | Docker logs |
| uploaded files | `data/files/` |
| smoke logs | `logs/smoke-p0.log` |

常用命令：

```powershell
docker compose ps
docker compose logs backend
docker compose logs postgres
curl http://localhost:8000/api/v1/health
```

排错顺序：

1. 看 `docker compose ps`。
2. 看 backend health。
3. 看 migration 日志。
4. 看数据库连接。
5. 看 Provider 配置。
6. 看前端 API base URL。

## 14. CI 预留

P0 可以先不接 CI，但仓库结构要支持后续加入：

| Job | P1 内容 |
| --- | --- |
| backend-test | ruff、pytest、migration smoke |
| frontend-test | typecheck、lint、unit test |
| e2e-smoke | Playwright + docker compose |
| docs-check | Mermaid render、链接检查 |

CI 原则：

- 默认不调用真实 Qwen。
- 使用 Fake Provider。
- 使用临时 PostgreSQL。
- 上传文件使用 demo fixture。

## 15. 安全与数据边界

P0 必须遵守：

- `.env` 不提交。
- 上传文件目录不提交。
- demo 文件不能包含真实企业敏感信息。
- 日志不输出 API Key。
- smoke 输出不包含密钥。
- 前端环境变量只允许 `NEXT_PUBLIC_` 安全变量。

## 16. P0 验收标准

DevOps / Demo P0 必须通过：

- `docker compose up postgres` 后数据库可连接。
- pgvector extension 已安装。
- `alembic upgrade head` 可从空库执行成功。
- 后端 health 返回成功。
- 前端 dev server 可访问。
- demo 文件存在。
- smoke 脚本至少跑通 Markdown 主链路。
- 演示前检查清单全部完成。
- Provider 故障时可以切 Fake Provider。

## 17. 与前序文档对齐

| 来源文档 | 本文承接 |
| --- | --- |
| `09-acceptance-test-spec.md` | 落地 P0 验收环境、演示数据和主剧本 |
| `11-backend-implementation-spec.md` | 落地 PostgreSQL、pgvector、migration、后端启动和健康检查 |
| `12-frontend-implementation-spec.md` | 落地 Next.js 启动、API base URL、E2E smoke 和前端演示 |

## 18. 后续动作

第 13 篇完成后，建议进入工程骨架实现：

1. 创建 `backend/` FastAPI 脚手架。
2. 创建 `frontend/` Next.js 脚手架。
3. 创建 `docker-compose.yml`、`.env.example` 和 `docker/postgres/init.sql`。
4. 创建 `data/demo/` 和 smoke 脚本。
5. 跑通 P0 最小闭环。
