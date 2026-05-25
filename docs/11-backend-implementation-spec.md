# KnowWeave 后端实现规格说明书

版本：v0.1
日期：2026-05-25
状态：草案
关联文档：`docs/03-system-architecture-spec.md`、`docs/04-data-model-spec.md`、`docs/05-ingestion-spec.md`、`docs/06-llm-wiki-spec.md`、`docs/07-search-and-chat-spec.md`、`docs/10-evaluation-spec.md`

## 0. 文档边界

本文定义 KnowWeave P0 后端如何从 Spec 落到可开发代码，包括：

- FastAPI 项目结构。
- PostgreSQL + pgvector 初始化和迁移策略。
- SQLAlchemy model、Pydantic schema、Service 层和 API 层边界。
- 文件上传、解析、分块、检索、问答、Wiki、反馈和评测样本的 P0 实现路径。
- Qwen Provider 抽象和后续多 Provider 扩展口。
- SSE 流式回答、任务状态、错误处理、日志和测试策略。

本文不负责：

- 前端页面、组件和状态管理，见后续 `12-frontend-implementation-spec.md`。
- Docker Compose、部署脚本和演示数据，见后续 `13-devops-and-demo-spec.md`。
- 完整多模态深度解析、向量检索、评测运行平台和权限系统；这些属于 P1/P2。

## 1. 实现目标

第 11 篇的目标是让后端开发可以直接开工，而不需要重新解释前 10 篇文档。

P0 后端必须做到：

- 提供稳定 API，让前端可以完成上传、解析、chunk 治理、搜索、Wiki、Chat、Feedback 和 Evaluation Sample 主链路。
- 按 `04-data-model-spec.md` 落地核心关系表和索引。
- 使用 PostgreSQL 关系表和全文检索完成 MVP，不强制启用 embedding。
- 通过 Provider 抽象调用 Qwen，不在业务 Service 中绑定厂商 SDK。
- 保证所有 AI 输出、检索结果、引用和反馈可追溯到 source span。
- 为 P1 的 pgvector、Web 模型配置页面、Wiki Revision diff、后台任务、评测运行保留扩展口。

## 2. 优先级边界

| 层级 | 后端必须完成 | 暂不完成 |
| --- | --- | --- |
| P0 | FastAPI、PostgreSQL、Alembic、关系表、文件上传、本地存储、基础解析、chunking、关键词搜索、SSE Chat、Document Wiki、Feedback、Evaluation Sample Candidate | Web 模型配置页面、向量检索、后台队列、复杂权限、多租户 |
| P1 | pgvector embedding、hybrid search、任务队列、WebSocket 任务推送、Wiki Revision diff/rollback、Evaluation Runs、模型配置页面 | 自动修复、复杂多模型竞赛、细粒度 RBAC |
| P2 | 多模态 parser、ASR/OCR/Vision Provider、知识图谱、自动回归评测、权限协作、对象存储 | 完全自动替代人工治理 |

## 3. 后端技术栈

| 类型 | P0 选择 | 说明 |
| --- | --- | --- |
| Web Framework | FastAPI | 类型清晰，适合 API、SSE、文件上传和异步调用 |
| Runtime | Python 3.11+ | 与解析、AI Provider、数据库生态匹配 |
| ORM | SQLAlchemy 2.x | 使用 typed declarative models |
| Migration | Alembic | 每次数据模型变更必须迁移化 |
| Schema | Pydantic v2 | API request/response 和内部 DTO |
| Database | PostgreSQL 15+ | 关系数据和全文检索 |
| Vector Extension | pgvector | P0 安装扩展但不强制使用 |
| File Storage | Local filesystem | P0 本地存储，P1/P2 抽象对象存储 |
| LLM Provider | Qwen / DashScope | P0 默认模型族 |
| HTTP Client | httpx | 调用 Qwen/OpenAI-compatible API |
| Test | pytest + pytest-asyncio | 单元、API、Service、数据库测试 |
| Lint / Format | ruff | P0 建议启用 |

## 4. 项目目录结构

建议后端目录放在 `backend/` 下：

```text
backend/
  app/
    main.py
    core/
      config.py
      logging.py
      errors.py
      security.py
      pagination.py
      time.py
    db/
      session.py
      base.py
      init.py
      types.py
    models/
      knowledge_file.py
      parse_result.py
      document_block.py
      chunk.py
      source_span.py
      knowledge_unit.py
      wiki.py
      citation.py
      chat.py
      feedback.py
      evaluation.py
      tag.py
      provider_config.py
    schemas/
      files.py
      ingestion.py
      chunks.py
      search.py
      chat.py
      wiki.py
      feedback.py
      evaluation.py
      common.py
    api/
      deps.py
      router.py
      v1/
        files.py
        chunks.py
        search.py
        chat.py
        wiki.py
        feedback.py
        evaluation.py
        providers.py
        health.py
    services/
      file_service.py
      parsing_service.py
      chunk_service.py
      index_service.py
      search_service.py
      knowledge_unit_service.py
      wiki_service.py
      chat_service.py
      feedback_service.py
      evaluation_service.py
      task_service.py
    providers/
      base.py
      qwen.py
      openai_compatible.py
      storage.py
      parsers/
        base.py
        text_parser.py
        markdown_parser.py
        pdf_text_parser.py
        docx_text_parser.py
    repositories/
      files.py
      chunks.py
      search.py
      wiki.py
      chat.py
      feedback.py
      evaluation.py
    jobs/
      ingestion_jobs.py
      indexing_jobs.py
      wiki_jobs.py
      evaluation_jobs.py
    prompts/
      chat_qa_v1.md
      document_wiki_v1.md
      ku_extract_v1.md
    tests/
      unit/
      integration/
      api/
  alembic/
    versions/
  alembic.ini
  pyproject.toml
  README.md
```

目录原则：

- `api/` 只处理 HTTP、认证、参数校验、响应包装和异常映射。
- `services/` 承载业务流程和事务边界。
- `repositories/` 封装复杂查询，避免 Service 中堆 SQL。
- `models/` 只定义数据库结构和关系，不放业务方法。
- `schemas/` 只定义 API DTO，不直接暴露 ORM model。
- `providers/` 只适配外部服务，不保存业务状态。
- `jobs/` 预留异步任务入口，P0 可以同步调用。

## 5. 分层架构

```mermaid
flowchart TB
  Client["Frontend / API Client"] --> API["FastAPI API Layer"]
  API --> Services["Application Services"]
  Services --> Repos["Repositories"]
  Repos --> DB["PostgreSQL + pgvector"]
  Services --> Providers["Provider Layer"]
  Providers --> Qwen["Qwen / DashScope"]
  Providers --> Storage["Local File Storage"]
  Services --> Jobs["P0 Inline Jobs / P1 Queue"]
  Jobs --> Services
```

调用规则：

- API 可以调用 Service，不直接调用 Repository。
- Service 可以调用 Repository、Provider、Job helper。
- Repository 可以访问 SQLAlchemy Session，不调用 Service。
- Provider 不知道数据库表结构。
- Job 不绕过 Service；即使异步执行，也复用同一套业务 Service。

## 6. 配置与环境变量

P0 必需环境变量：

| 变量 | 必填 | 示例 | 说明 |
| --- | --- | --- | --- |
| `APP_ENV` | 否 | `development` | development/test/production |
| `DATABASE_URL` | 是 | `postgresql+psycopg://user:pass@localhost:5432/knowweave` | 主数据库 |
| `FILE_STORAGE_ROOT` | 是 | `./data/files` | 原始文件存储根目录 |
| `QWEN_API_KEY` | 是 | `sk-...` | Qwen API Key |
| `QWEN_BASE_URL` | 否 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | OpenAI-compatible 地址 |
| `QWEN_CHAT_MODEL` | 否 | `qwen-plus` | Chat 和 Wiki 生成默认模型 |
| `QWEN_GENERATION_MODEL` | 否 | `qwen-plus` | 文档生成默认模型 |
| `QWEN_TIMEOUT_SECONDS` | 否 | `60` | Provider 调用超时 |
| `MAX_UPLOAD_MB` | 否 | `50` | P0 上传限制 |
| `ENABLE_PGVECTOR` | 否 | `true` | P0 安装扩展，P1 启用向量 |

配置规则：

- `core/config.py` 使用 Pydantic Settings。
- 禁止在代码中硬编码 API Key、模型名、数据库地址。
- P0 可以不落地 `model_provider_configs` Web 配置，但启动时应能生成默认 Provider 配置对象。
- 配置读取失败必须在启动阶段 fail fast，而不是在用户请求时才报错。

## 7. 数据库落地策略

### 7.1 迁移顺序

Alembic 迁移建议按以下顺序拆分：

1. `0001_enable_extensions`
   - `CREATE EXTENSION IF NOT EXISTS vector`
   - `CREATE EXTENSION IF NOT EXISTS pg_trgm`，可选
2. `0002_core_files_and_parsing`
   - `knowledge_files`
   - `parse_results`
   - `document_blocks`
   - `timeline_blocks`
3. `0003_chunks_and_sources`
   - `chunks`
   - `source_spans`
4. `0004_knowledge_and_wiki`
   - `knowledge_units`
   - `knowledge_unit_sources`
   - `wiki_pages`
   - `wiki_revisions`
   - `wiki_page_units`
   - `citations`
5. `0005_search_chat_feedback`
   - `chat_sessions`
   - `chat_messages`
   - `retrieved_contexts`
   - `feedback`
6. `0006_evaluation_and_tags`
   - `evaluation_samples`
   - `tags`
   - `tag_bindings`
   - `model_provider_configs`

### 7.2 SQLAlchemy Model 规则

Model 必须遵守：

- 表名与 `04-data-model-spec.md` 一致。
- `id` 使用 UUID。
- `created_at`、`updated_at` 使用 timezone-aware timestamp。
- JSONB 字段必须在 schema 层定义允许结构。
- 枚举字段先使用 string enum，避免过早绑定数据库 enum 迁移成本。
- 软删除对象必须保留 `deleted_at` 或 `status`。

### 7.3 全文检索

P0 使用 PostgreSQL full text search：

- `knowledge_files.search_text`
- `chunks.search_text`
- `knowledge_units.search_text`
- `wiki_pages.search_text`

推荐实现方式：

- Service 层更新对象内容时同步更新 `search_text`。
- Repository 层使用 `to_tsvector('simple', search_text)` 或 `plainto_tsquery('simple', query)`。
- 中文分词 P0 不做复杂优化；可结合 `ILIKE` 兜底。
- Search Result metadata 预留 `score_breakdown`。

P1 再启用：

- embedding 字段。
- pgvector index。
- hybrid score。
- rerank provider。

## 8. API 总览

P0 API 前缀统一为 `/api/v1`。

| 模块 | Endpoint | P0 | Service |
| --- | --- | --- | --- |
| Health | `GET /health` | 是 | Health |
| Files | `POST /files/upload` | 是 | FileService |
| Files | `GET /files` | 是 | FileService |
| Files | `GET /files/{file_id}` | 是 | FileService |
| Files | `DELETE /files/{file_id}` | 是 | FileService |
| Ingestion | `POST /files/{file_id}/parse` | 是 | ParsingService |
| Ingestion | `POST /files/{file_id}/reparse` | P1 | ParsingService |
| Blocks | `GET /files/{file_id}/document-blocks` | 是 | ParsingService |
| Chunks | `GET /files/{file_id}/chunks` | 是 | ChunkService |
| Chunks | `GET /chunks/{chunk_id}` | 是 | ChunkService |
| Chunks | `PATCH /chunks/{chunk_id}` | 是 | ChunkService |
| Chunks | `POST /chunks/{chunk_id}/ignore` | 是 | ChunkService |
| Chunks | `POST /chunks/{chunk_id}/verify` | 是 | ChunkService |
| Chunks | `POST /files/{file_id}/rechunk` | 是 | ChunkService |
| Knowledge Units | `GET /knowledge-units` | 是 | KnowledgeUnitService |
| Knowledge Units | `GET /knowledge-units/{knowledge_unit_id}` | 是 | KnowledgeUnitService |
| Knowledge Units | `POST /knowledge-units` | 是 | KnowledgeUnitService |
| Knowledge Units | `PATCH /knowledge-units/{knowledge_unit_id}` | 是 | KnowledgeUnitService |
| Search | `POST /search` | 是 | SearchService |
| Search | `GET /search/runs/{retrieval_run_id}` | 是 | SearchService |
| Chat | `POST /chat/sessions` | 是 | ChatService |
| Chat | `GET /chat/sessions` | 是 | ChatService |
| Chat | `GET /chat/sessions/{session_id}` | 是 | ChatService |
| Chat | `POST /chat/sessions/{session_id}/messages` | 是 | ChatService |
| Chat | `GET /chat/messages/{message_id}/citations` | 是 | ChatService |
| Wiki | `POST /files/{file_id}/wiki` | 是 | WikiService |
| Wiki | `GET /wiki/pages` | 是 | WikiService |
| Wiki | `GET /wiki/pages/{wiki_page_id}` | 是 | WikiService |
| Wiki | `PATCH /wiki/pages/{wiki_page_id}` | 是 | WikiService |
| Feedback | `POST /feedback` | 是 | FeedbackService |
| Feedback | `GET /feedback` | 是 | FeedbackService |
| Evaluation | `POST /evaluation-samples` | 是 | EvaluationService |
| Evaluation | `GET /evaluation-samples` | 是 | EvaluationService |
| Evaluation | `PATCH /evaluation-samples/{sample_id}` | 是 | EvaluationService |
| Providers | `GET /providers/defaults` | P1 | ProviderConfigService |
| Providers | `POST /providers/test` | P1 | ProviderConfigService |

## 9. API 设计规范

### 9.1 响应包装

P0 推荐统一响应：

```json
{
  "data": {},
  "error": null,
  "request_id": "req_001"
}
```

错误响应：

```json
{
  "data": null,
  "error": {
    "code": "FILE_TYPE_NOT_SUPPORTED",
    "message": "Only txt, md, pdf and docx files are supported in MVP.",
    "details": {}
  },
  "request_id": "req_001"
}
```

### 9.2 分页

列表接口使用：

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `page` | `1` | 从 1 开始 |
| `page_size` | `20` | 最大 100 |
| `sort` | `created_at_desc` | 明确白名单 |

响应：

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 0
}
```

### 9.3 幂等与并发

P0 幂等规则：

- 文件上传使用 `sha256` 识别重复文件，P0 可以只提示疑似重复，不强制去重。
- `parse` 对正在解析的文件返回当前状态，不重复创建并发解析。
- `rechunk` 创建新 chunk 时必须归档旧 chunk 或标记旧策略版本。
- `PATCH /chunks/{id}` 需要 `updated_at` 或 `version` 预留并发控制，P0 可先记录最后写入。

## 10. Service 边界

### 10.1 FileService

职责：

- 校验文件类型、大小和文件名。
- 计算 sha256。
- 保存原始文件到 `FILE_STORAGE_ROOT`。
- 创建 `knowledge_files`。
- 处理软删除。
- 返回文件详情统计：parse status、block count、chunk count、warning count。

不得做：

- 不解析文件内容。
- 不直接生成 chunk。
- 不调用 LLM。

### 10.2 ParsingService

职责：

- 根据 file_type 选择 Parser。
- 创建 `parse_results`。
- 写入 `document_blocks`。
- 保存 parser warnings 和 metadata。
- 将文件状态从 uploaded 推进到 parse_succeeded 或 parse_failed。

P0 Parser：

- `TextParser`
- `MarkdownParser`
- `PdfTextParser`
- `DocxTextParser`

P0 对表格、图片、公式、代码：

- 可以生成 `document_blocks.block_type` placeholder。
- 不做深度结构化理解。
- 不丢弃位置和提示信息。

### 10.3 ChunkService

职责：

- 基于 document_blocks 生成 chunks。
- 写入 source_spans。
- 支持 hybrid chunking 默认策略。
- 支持 chunk 查看、编辑、忽略、确认。
- 维护 `raw_content`、`edited_content`、`search_text`。
- 生成 `quality_flags`。

P0 默认参数：

| 参数 | 默认 |
| --- | --- |
| `strategy` | `hybrid` |
| `max_chars` | 1200 |
| `min_chars` | 80 |
| `overlap_chars` | 120 |
| `include_headings` | true |
| `respect_block_boundary` | true |
| `split_separators` | `["\n\n", "。", "；", ".", "\n"]` |

### 10.4 IndexService

职责：

- 更新 file、chunk、Knowledge Unit、Wiki 的 `search_text`。
- 为全文检索提供统一 query builder。
- P1 扩展 embedding 生成和 pgvector index。

P0 IndexService 不应：

- 调用 LLM 生成 embedding。
- 做复杂 rerank。
- 直接拼接未转义 SQL。

### 10.5 SearchService

职责：

- 生成 `retrieval_run_id`。
- 检索 file、chunk、Knowledge Unit、Wiki。
- 应用默认过滤：soft_deleted、ignored、archived。
- 写入 `retrieved_contexts`。
- 返回统一 Search Result。

P0 不单独创建 `retrieval_runs` 表。`retrieval_run_id` 是 `retrieved_contexts` 的分组 ID，`GET /search/runs/{retrieval_run_id}` 通过该分组 ID 派生查询本次检索的 query、参数快照和结果列表。P1 如需记录运行状态、耗时、失败原因或评测关联，再独立引入 `retrieval_runs` 表。

P0 排序：

1. 文本匹配分。
2. 对象类型权重。
3. `curation_status`。
4. 更新时间。

P1 再加入：

- embedding score。
- hybrid score。
- rerank score。
- parent-child context expansion。

### 10.6 WikiService

职责：

- 基于文件、chunks、Knowledge Units 生成 Document Wiki。
- 调用 LLMProvider。
- 保存 `wiki_pages`。
- 写入 citations。
- 支持 Wiki 编辑、状态流转和 source_available 展示。
- P0 可覆盖当前 `content_markdown`，P1 启用 `wiki_revisions` diff/rollback。

Document Wiki 生成输入：

- file metadata。
- selected chunks。
- optional knowledge_units。
- source spans。
- generation prompt version。

输出必须包含：

- title。
- content_markdown。
- citations。
- status = draft。
- metadata，包括 prompt_version、model_name、source_file_id。

### 10.7 ChatService

职责：

- 创建 chat session。
- 接收用户 message。
- 调用 SearchService 获取上下文。
- 调用 LLMProvider stream。
- 转换为 KnowWeave SSE 事件。
- 保存完整 answer_markdown。
- 写入 citations 和 retrieved_contexts。

ChatService 不应：

- 直接透传 Qwen 原始流事件。
- 自行绕过 SearchService 选择上下文。
- 在前端完成后才保存答案；必须后端累积最终答案。

### 10.8 FeedbackService

职责：

- 保存 answer、citation、chunk、wiki、retrieval feedback。
- 关联 message、citation、chunk、wiki_page、retrieval_run_id。
- 为 EvaluationService 提供候选样本来源。
- 触发 quality_flags 或待处理列表更新。

P0 支持 feedback_type：

- answer_helpful。
- answer_wrong。
- citation_helpful。
- citation_wrong。
- retrieval_helpful。
- chunk_low_quality。
- wiki_needs_update。
- retrieval_missing。
- retrieval_irrelevant。

### 10.9 EvaluationService

职责：

- 从人工输入创建 evaluation sample。
- 从 chat message 创建 candidate。
- 从 feedback 创建 candidate。
- 保存 question、actual_answer、expected_answer、retrieved_contexts_snapshot、citations_snapshot、feedback_snapshot。
- 支持 candidate、draft、verified、rejected、archived 状态。

P0 不负责：

- 批量 evaluation run。
- 自动指标计算。
- LLM Judge 自动裁判。

### 10.10 TaskService

P0 可以不落独立 `task_runs` 表，但 Service 内部应有统一任务状态 DTO：

```json
{
  "task_id": "task_001",
  "task_type": "parsing",
  "status": "running",
  "progress": 0.42,
  "message": "Parsing page 12",
  "related_object_type": "file",
  "related_object_id": "file_001"
}
```

P1 引入队列后，TaskService 负责：

- 创建 task。
- 更新进度。
- 失败重试。
- WebSocket 推送。

## 11. Provider 抽象

### 11.1 接口列表

P0 必须定义：

```text
LLMProvider
StorageProvider
DocumentParser
```

P1/P2 预留：

```text
EmbeddingProvider
RerankProvider
VisionProvider
OCRProvider
ASRProvider
```

### 11.2 LLMProvider

接口语义：

| 方法 | P0 | 说明 |
| --- | --- | --- |
| `generate(messages, options)` | 是 | 非流式生成，用于 Wiki |
| `stream(messages, options)` | 是 | 流式生成，用于 Chat |
| `health_check()` | 是 | Provider 连通性 |

返回值必须规范化：

```json
{
  "content": "answer markdown",
  "model_name": "qwen-plus",
  "usage": {
    "input_tokens": 123,
    "output_tokens": 456
  },
  "raw_metadata": {}
}
```

流式事件必须规范化为：

```json
{
  "type": "delta",
  "text": "partial text",
  "finish_reason": null,
  "usage": null
}
```

### 11.3 Qwen Provider

QwenProvider 规则：

- 优先使用 OpenAI-compatible API 形态。
- Provider 内部处理 base_url、api_key、model_name、timeout、temperature、max_tokens。
- 任何 DashScope/Qwen SDK 类型不得出现在 Service 层。
- Provider 错误必须转换为 KnowWeave 错误码。

错误映射：

| Provider 错误 | KnowWeave 错误码 |
| --- | --- |
| 认证失败 | `PROVIDER_AUTH_FAILED` |
| 限流 | `PROVIDER_RATE_LIMITED` |
| 超时 | `PROVIDER_TIMEOUT` |
| 模型不存在 | `PROVIDER_MODEL_NOT_FOUND` |
| 内容安全拒绝 | `PROVIDER_CONTENT_REJECTED` |
| 未知错误 | `PROVIDER_UNKNOWN_ERROR` |

## 12. Ingestion 实现流程

P0 默认同步流程：

```mermaid
sequenceDiagram
  participant UI as Frontend
  participant API as Files API
  participant File as FileService
  participant Parse as ParsingService
  participant Chunk as ChunkService
  participant Index as IndexService
  participant DB as PostgreSQL

  UI->>API: POST /files/upload
  API->>File: validate and store
  File->>DB: insert knowledge_files
  API->>Parse: parse(file_id)
  Parse->>DB: insert parse_results and document_blocks
  Parse->>Chunk: generate chunks
  Chunk->>DB: insert chunks and source_spans
  Chunk->>Index: update search_text
  Index->>DB: update searchable fields
  API-->>UI: file detail with status
```

失败规则：

- 文件已保存但解析失败：保留 `knowledge_files`，状态为 parse_failed。
- Parser 抛错：写入 `parse_results.error_code` 和 `error_message`。
- Chunking 抛错：文件进入 parse_succeeded 但 chunk_status 可标记失败，P0 也可整体 parse_failed。
- 所有失败必须可重试。

## 13. Search 与 Chat 实现

### 13.1 Search Request

```json
{
  "query": "请假审批规则",
  "target_types": ["file", "chunk", "knowledge_unit", "wiki_page"],
  "filters": {
    "source_available": true
  },
  "top_k": 10
}
```

### 13.2 Search Response

`GET /search/runs/{retrieval_run_id}` 返回的数据从 `retrieved_contexts` 派生。后端必须保证同一次 Search 或 Chat 召回写入的多条 `retrieved_contexts` 共享同一个 `retrieval_run_id`。

```json
{
  "retrieval_run_id": "run_001",
  "results": [
    {
      "result_type": "chunk",
      "result_id": "chunk_001",
      "title": "员工手册 / 请假制度",
      "snippet": "3 天以内由直属主管审批...",
      "score": 0.82,
      "source_available": true,
      "source_locator": {
        "file_id": "file_001",
        "chunk_id": "chunk_001",
        "page_number": 12
      }
    }
  ]
}
```

### 13.3 Chat SSE

Chat API 使用 `text/event-stream`。

事件顺序：

```text
event: start
data: {"message_id":"msg_001","retrieval_run_id":"run_001"}

event: retrieval
data: {"retrieval_run_id":"run_001","results":[...]}

event: delta
data: {"text":"根据员工手册..."}

event: citations
data: {"citations":[...]}

event: done
data: {"message_id":"msg_002","finish_reason":"stop"}
```

错误事件：

```text
event: error
data: {"code":"PROVIDER_TIMEOUT","message":"LLM provider timed out."}
```

后端规则：

- `start` 之前必须已经创建用户 message。
- `retrieval` 事件之前必须完成 SearchService 检索并写入 retrieved_contexts。
- `delta` 过程中后端累积 answer buffer。
- `done` 前保存 assistant message、citations、usage metadata。
- 出错时如果已有 partial answer，应保存 partial 状态或错误 metadata。

## 14. Wiki 实现

### 14.1 Document Wiki 生成

API：

```text
POST /api/v1/files/{file_id}/wiki
```

Request：

```json
{
  "source_chunk_ids": ["chunk_001", "chunk_002"],
  "generation_mode": "document_summary",
  "prompt_version": "document_wiki_v1"
}
```

Service 流程：

1. 校验 file 存在且未软删除。
2. 查询可搜索且未忽略 chunks。
3. 组织 prompt input。
4. 调用 LLMProvider.generate。
5. 解析输出 Markdown。
6. 写入 `wiki_pages`。
7. 写入 `citations`。
8. 返回 draft Wiki。

### 14.2 Wiki 编辑

API：

```text
PATCH /api/v1/wiki/pages/{wiki_page_id}
```

Request：

```json
{
  "title": "员工请假制度",
  "content_markdown": "...",
  "change_summary": "修正审批角色说明",
  "status": "pending_review"
}
```

P0 规则：

- `change_summary` 必填。
- 更新 `wiki_pages.content_markdown`。
- `wiki_revisions` 表可预留但不要求 diff UI。
- 若 citation key 被删除，Service 不自动删除历史 citation，但应记录 warning。

## 15. Feedback 与 Evaluation 实现

### 15.1 Feedback 写入

API：

```text
POST /api/v1/feedback
```

Request：

```json
{
  "target_type": "citation",
  "target_id": "citation_001",
  "feedback_type": "citation_wrong",
  "comment": "引用没有支撑该结论",
  "metadata": {
    "message_id": "msg_001",
    "retrieval_run_id": "run_001"
  }
}
```

Service 规则：

- target 必须存在。
- feedback 写入后不直接修改原对象内容。
- 负反馈进入待处理列表。
- citation_wrong 可触发 evaluation sample candidate 创建入口。

### 15.2 Evaluation Sample Candidate

从 Chat 生成：

```text
POST /api/v1/chat/messages/{message_id}/to-evaluation-sample
```

从 Feedback 生成：

```text
POST /api/v1/feedback/{feedback_id}/to-evaluation-sample
```

Candidate 必须保存：

- question。
- actual_answer。
- retrieved_contexts_snapshot。
- citations_snapshot。
- feedback_snapshot。
- expected_source_hint，可为空。
- status = candidate。

## 16. 错误码

| 错误码 | HTTP | 场景 |
| --- | --- | --- |
| `VALIDATION_ERROR` | 422 | 参数校验失败 |
| `FILE_TYPE_NOT_SUPPORTED` | 400 | 不支持的文件类型 |
| `FILE_TOO_LARGE` | 400 | 超过上传限制 |
| `FILE_NOT_FOUND` | 404 | 文件不存在或已删除 |
| `PARSE_FAILED` | 500 | 解析失败 |
| `CHUNK_NOT_FOUND` | 404 | chunk 不存在 |
| `SOURCE_UNAVAILABLE` | 409 | 来源文件不可用 |
| `SEARCH_FAILED` | 500 | 检索失败 |
| `CHAT_STREAM_FAILED` | 500 | Chat 流式失败 |
| `PROVIDER_TIMEOUT` | 504 | Provider 超时 |
| `PROVIDER_AUTH_FAILED` | 502 | Provider 鉴权失败 |
| `WIKI_GENERATION_FAILED` | 500 | Wiki 生成失败 |
| `FEEDBACK_TARGET_NOT_FOUND` | 404 | 反馈对象不存在 |
| `EVALUATION_SAMPLE_INVALID` | 400 | 样本字段不完整 |

## 17. 安全与权限

P0 可以是单用户模式，但后端仍需保留权限扩展点：

- 所有核心表预留 `created_by`、`updated_by` 可选字段或 metadata。
- API deps 中预留 `get_current_user()`。
- SearchService 预留 permission filter hook。
- Feedback 和 Evaluation 不应暴露无权限 source text。
- 文件路径不得直接使用用户上传文件名。
- 所有下载或 source viewer 请求必须通过 file_id 查存储路径。

P0 文件安全：

- 限制文件类型。
- 限制文件大小。
- 文件名只作为展示字段。
- 存储路径使用系统生成 UUID。
- 不执行上传文件中的任何脚本或宏。

## 18. 可观察性

P0 日志字段：

| 字段 | 说明 |
| --- | --- |
| `request_id` | 每个 HTTP 请求唯一 ID |
| `user_id` | P0 可为空 |
| `file_id` | 文件相关操作 |
| `retrieval_run_id` | 搜索和 Chat 召回 |
| `message_id` | Chat |
| `provider_name` | LLM 调用 |
| `model_name` | 模型名 |
| `duration_ms` | 耗时 |
| `error_code` | 错误码 |

关键日志：

- 文件上传成功/失败。
- parser 开始/完成/失败。
- chunk 生成数量和质量 flags。
- search query、top_k、result_count。
- chat start、provider duration、token usage。
- wiki generation duration。
- feedback 写入。
- evaluation sample 创建。

P1 可增加 metrics：

- request latency。
- provider latency。
- parse duration。
- search result count。
- feedback negative rate。
- evaluation candidate count。

## 19. 测试策略

### 19.1 单元测试

必须覆盖：

- chunking strategy。
- source span 写入。
- search result ranking。
- citation 构造。
- feedback 到 evaluation sample 转换。
- provider error mapping。

### 19.2 API 测试

必须覆盖：

- upload -> parse -> chunks。
- edit chunk -> search_text 更新。
- search -> retrieval_run_id -> retrieved_contexts。
- chat SSE event order。
- wiki generation mock provider。
- feedback write。
- evaluation sample candidate creation。

### 19.3 数据库测试

必须覆盖：

- Alembic migration 可以从空库跑通。
- soft delete 后默认查询不可见。
- ignored chunk 不参与搜索。
- source span 与 chunk 关联完整。
- retrieved_contexts 有 retrieval_run_id。

### 19.4 Provider 测试

P0 使用 fake provider：

- `FakeLLMProvider.generate()` 返回固定 Markdown。
- `FakeLLMProvider.stream()` 返回固定 delta 序列。
- API 测试默认不调用真实 Qwen。

真实 Qwen 测试：

- 放到 integration tests。
- 需要 `QWEN_API_KEY`。
- CI 默认跳过。

## 20. 本地启动

后续 DevOps 文档会定义完整 Docker Compose。P0 后端文档先约定最小命令：

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Windows PowerShell：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

健康检查：

```text
GET http://localhost:8000/api/v1/health
```

## 21. P0 实现里程碑

| 顺序 | 任务 | 产出 | 验收 |
| --- | --- | --- | --- |
| 1 | 后端脚手架 | FastAPI app、配置、日志、错误处理 | health API 可访问 |
| 2 | 数据库基础 | SQLAlchemy、Alembic、核心表迁移 | 空库 migration 成功 |
| 3 | 文件上传 | FileService、LocalStorageProvider | 文件入库并保存 |
| 4 | Parser | text/md/pdf/docx parser adapter | parse_results 和 blocks 可见 |
| 5 | Chunking | ChunkService、source_spans | chunk 可查看和编辑 |
| 6 | Search | IndexService、SearchService | 关键词返回 file/chunk/wiki |
| 7 | Provider | QwenLLMProvider、FakeLLMProvider | fake 测试通过，Qwen 可连通 |
| 8 | Chat SSE | ChatService、SSE protocol | 前端可流式消费 |
| 9 | Wiki | Document Wiki generation | wiki draft 可生成和编辑 |
| 10 | Feedback | FeedbackService | answer/citation/chunk/wiki feedback 可保存 |
| 11 | Evaluation Candidate | EvaluationService | feedback/chat 可转样本 |
| 12 | P0 Smoke | 端到端脚本 | 演示主链路跑通 |

## 22. P0 验收标准

后端 P0 必须通过：

- 空数据库可以执行全部 Alembic migration。
- 上传 Markdown 文件后可以生成 document_blocks、chunks、source_spans。
- 上传 PDF 后至少可以生成文本 blocks，并保留 page_number 或 source locator。
- 用户可以编辑 chunk，edited_content 不覆盖 raw_content。
- ignored chunk 默认不参与搜索、Chat 和 Wiki 生成。
- Search API 返回 retrieval_run_id，并写入 retrieved_contexts。
- Chat API 返回 SSE start、retrieval、delta、citations、done。
- Chat 完成后数据库保存 user message、assistant message、citations。
- Document Wiki 可以基于文件生成 draft。
- Wiki 编辑必须保存 change_summary。
- Feedback 可以关联 message、citation、chunk 或 wiki。
- Feedback 或 Chat 可以生成 evaluation sample candidate。
- Provider 错误不会把厂商原始异常直接暴露给前端。

## 23. 与前序文档对齐

| 来源文档 | 本文承接 |
| --- | --- |
| `03-system-architecture-spec.md` | 落地 FastAPI、Service Layer、Provider Layer、SSE、任务策略 |
| `04-data-model-spec.md` | 落地 PostgreSQL、SQLAlchemy models、Alembic migration、索引 |
| `05-ingestion-spec.md` | 落地上传、解析、Document Block、chunking、source span |
| `06-llm-wiki-spec.md` | 落地 Document Wiki 生成、编辑、citation、revision 预留 |
| `07-search-and-chat-spec.md` | 落地 Search、retrieval_run_id、retrieved_contexts、Chat SSE、Feedback |
| `10-evaluation-spec.md` | 落地 evaluation sample candidate，预留 evaluation_runs |

## 24. 后续文档

第 11 篇完成后，后续建议继续：

1. `12-frontend-implementation-spec.md`
   - 定义 Next.js 页面路由、组件拆分、API client、SSE 消费、状态管理和前端测试。
2. `13-devops-and-demo-spec.md`
   - 定义 Docker Compose、PostgreSQL + pgvector 初始化、环境变量、演示数据、启动脚本和答辩演示流程。
