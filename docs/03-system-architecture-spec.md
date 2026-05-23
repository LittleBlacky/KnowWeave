# KnowWeave 系统架构规格说明书

版本：v0.5
日期：2026-05-23  
状态：草案  
关联文档：`docs/01-product-spec.md`、`docs/02-knowledge-lifecycle-spec.md`

## 1. 文档目标

本文定义 KnowWeave 的系统架构、模块边界、技术选型、数据流和扩展策略。它将产品规格中的“LLM Wiki 知识库管理平台”和生命周期规格中的“上传、解析、分块、检索、沉淀、评估”落到可实现的工程结构。

本文回答以下问题：

- MVP 使用什么技术栈。
- 前端、后端、存储和 AI Provider 如何分层。
- 各核心模块的职责边界是什么。
- 文档处理、问答、反馈、Wiki 生成如何流动。
- 哪些能力 MVP 实现，哪些只保留扩展点。
- 如何参考 DeepParseX 的架构思想，但不复用其代码。

## 2. 架构原则

### 2.1 小而完整

MVP 优先完成端到端闭环，而不是追求企业级全量能力。系统应先支持本地或单机部署，保证演示稳定。

### 2.2 模块清晰

上传、解析、分块、索引、检索、问答、知识单元、Wiki、反馈评估应拆成独立模块，避免业务逻辑全部堆在 API 层。

### 2.3 AI 可替换

所有外部 AI 能力一旦接入，必须通过 Provider 抽象接入，不在业务代码里绑定具体厂商。MVP 仅启用 LLMProvider；EmbeddingProvider、RerankProvider、VisionProvider、OCRProvider、ASRProvider 等接口先预留，按 P1/P2 逐步启用。

### 2.4 原文可追溯

所有 chunk、Knowledge Unit、Wiki 和 Answer Citation 都必须能回溯到原始文件或人工来源。架构中必须保留 source span。

### 2.5 扩展先留口，MVP 不过度实现

表格、图片、公式、代码、音视频等多类型内容在架构上预留 parser 和 typed chunk，但 MVP 主要实现文本处理。

## 3. 总体架构

MVP 采用前后端分离架构：

```text
Web App
  -> API Server
      -> Application Services
          -> Document Pipeline
          -> Knowledge Curation
          -> Search and Chat
          -> Wiki Generation
          -> Evaluation
      -> Database
      -> File Storage
      -> AI Providers
```

推荐逻辑分层：

```text
Frontend Layer
API Layer
Service Layer
Domain Layer
Infrastructure Layer
Provider Layer
```

## 4. MVP 技术选型

### 4.1 前端

推荐：

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- lucide-react
- react-markdown
- remark-gfm
- Server-Sent Events client

理由：

- 适合快速构建管理台。
- 与当前参考前端技术栈接近，学习成本低。
- 支持文档管理、列表、详情、编辑器、问答界面等复杂交互。

前端关键能力选型：

- Markdown 渲染：使用 `react-markdown` + `remark-gfm`，用于 Wiki 页面、问答答案、引用内容和知识单元预览。
- Markdown 编辑：MVP 使用 textarea + markdown preview，P1 可升级为 TipTap、Milkdown 或 Monaco-based Markdown editor。
- 流式回答：MVP 使用 SSE（Server-Sent Events），用于 LLM 单向流式输出；WebSocket 保留为 P1/P2 的任务状态推送通道，用于解析、分块、索引、Wiki 生成、评测运行等长任务状态更新。
- 流式 Markdown 渲染：服务端通过 SSE 推送 `delta`、`citations`、`done` 事件；前端累积 `answer_markdown`，以 50 到 100ms 节流方式使用 `react-markdown` 渲染。流式过程中可关闭复杂代码高亮，完成后进行最终 Markdown 渲染和引用挂载。
- PDF / 原文定位：P1 使用 PDF.js 或 react-pdf 支持页码跳转和 bbox 高亮；MVP 至少展示 source span 并支持跳转到文件/页码。
- Chunk 编辑：MVP 使用表单面板和 textarea，展示 raw_content、edited_content、source_spans、质量信号和关联对象。
- 表格与列表：MVP 可使用普通表格组件，P1 可引入 TanStack Table 支持复杂筛选、排序和批量操作。
- 代码高亮：P1 可引入 rehype-highlight 或 Shiki，用于代码 chunk、Wiki 和问答答案中的代码块。

不在架构文档展开的内容：

- 具体页面布局。
- 组件状态机。
- 编辑器快捷键。
- PDF 高亮坐标换算细节。
- SSE 消息格式。

这些内容放入 `docs/08-frontend-spec.md` 进一步定义。

### 4.2 后端

推荐：

- FastAPI
- Python 3.11+
- SQLAlchemy
- Pydantic

理由：

- 适合文件解析、AI Provider 调用和 API 开发。
- Python 生态有较多 PDF、DOCX、Markdown、Embedding、LLM SDK。
- 与参考项目后端风格接近，但可以从零实现更小的模块。

### 4.3 数据库

MVP 推荐：

- PostgreSQL
- pgvector

可选本地简化方案：

- SQLite，仅用于极简离线 Demo，不作为主推方案。

理由：

- KnowWeave 的核心对象包含文件、Document Block、Timeline Block、Chunk、Source Span、Knowledge Unit、Wiki、Feedback、Evaluation Sample，关系模型较强，PostgreSQL 更适合承载。
- 项目后续需要向量检索，直接使用 pgvector 可以减少从 SQLite 迁移的成本。
- PostgreSQL full text search 可以支持基础关键词检索，pgvector 可以支持语义检索。
- MVP 数据库基线包含 pgvector 扩展，但 MVP 仅使用 PostgreSQL 关系表和全文检索；Embedding 字段、向量索引和语义检索在 P1 启用。

### 4.4 文件存储

MVP 推荐：

- 本地文件系统

P1 可升级：

- MinIO
- S3 compatible storage

设计要求：

- 原始文件和解析资产分开存储。
- 文件记录保存 storage_path。
- 不在数据库中直接保存大文件二进制。

### 4.5 AI Provider

MVP 推荐：

- Qwen / DashScope Chat Model
- Qwen / DashScope Embedding Model，P1 启用
- Qwen / DashScope Rerank Model，可选

Provider 需要支持：

- chat completion
- structured generation
- embedding，P1 启用
- rerank，可选
- vision understanding，占位
- audio / video understanding，占位

环境变量：

- `QWEN_API_KEY`
- `QWEN_BASE_URL`
- `QWEN_CHAT_MODEL`
- `QWEN_EMBEDDING_MODEL`
- `QWEN_RERANK_MODEL`
- `QWEN_VL_MODEL`
- `QWEN_OMNI_MODEL`

初始模型族建议：

- 文本生成：Qwen Chat 系列，用于问答、知识单元生成、Wiki 草稿生成。
- Embedding：Qwen Embedding 系列，用于 chunk、Knowledge Unit、Wiki 的向量表示，P1 启用。
- Rerank：Qwen Rerank 系列，用于检索结果重排。
- Vision：Qwen VL 系列，用于后续图片、图表、扫描页理解。
- Omni / Audio：Qwen Omni 或音频理解系列，用于后续音视频转写、理解和时间轴摘要。

约束：

- MVP 代码只依赖 `LLMProvider` 等抽象；`EmbeddingProvider`、`RerankProvider` 等接口先预留，P1 启用。不直接依赖具体 Qwen SDK 类型。
- 如果 Qwen API 提供 OpenAI-compatible 调用方式，优先复用通用 OpenAI-compatible client；否则通过 DashScope client 实现 Qwen Provider。
- 模型名称必须通过环境变量配置，不写死在业务代码中。
- Qwen 是默认模型族，不是唯一模型族。后续用户应能通过 Web 界面配置和切换不同用途的模型。

### 4.6 模型配置与选择

KnowWeave 需要支持用户在 Web 界面中配置 LLM Provider 和模型用途。MVP 可以先使用环境变量配置默认 Qwen 模型，P1 开始提供模型配置页面。

模型用途：

- chat：知识库问答。
- generation：知识单元生成、Wiki 草稿生成。
- embedding：chunk、Knowledge Unit、Wiki 向量化。
- rerank：检索结果重排。
- vision：图片、图表、扫描页理解。
- audio：音视频转写和理解。

配置项：

- provider_name：供应商名称，例如 qwen、openai_compatible、local。
- provider_type：chat、embedding、rerank、vision、audio。
- base_url。
- api_key，必须加密存储或通过环境变量引用。
- model_name。
- enabled。
- is_default。
- timeout_seconds。
- max_tokens。
- temperature，适用于生成类模型。

用户操作：

- 新增模型 Provider。
- 测试 Provider 连通性。
- 为不同用途选择默认模型。
- 启用或停用 Provider。
- 查看模型调用失败原因。

运行规则：

- 系统启动时读取环境变量生成默认 Qwen Provider。
- 如果数据库中存在用户配置，则优先使用用户配置。
- 每一种用途必须最多只有一个默认 Provider。
- Provider 切换不应影响已有知识数据的可读性。
- Embedding 模型切换后，应标记受影响索引需要重新生成。

MVP/P1 边界：

- MVP：使用环境变量配置 Qwen 默认 chat/generation 模型。
- P1：提供 Web 模型配置页面，支持 OpenAI-compatible Provider。
- P2：支持本地模型、Ollama、vLLM、自部署 embedding 和多 Provider fallback。

### 4.7 LLM 应用框架

MVP 不直接引入 LlamaIndex、LangChain 或 LangGraph 作为核心依赖。

原因：

- KnowWeave 的核心差异是 chunk 可视化治理、source span、知识单元确认、Wiki 沉淀和反馈评估闭环，需要保持核心 pipeline 可解释、可控。
- 直接使用框架默认 RAG pipeline 容易隐藏分块、检索、上下文组织和评估细节。
- MVP 阶段 FastAPI Service + Provider 抽象足以完成端到端闭环。

预留 Adapter：

- LlamaIndexAdapter：后续用于增强 reader、index、query engine 和复杂 RAG。
- LangChainAdapter：后续用于复用特定 loader、splitter、retriever 或 tool 生态。
- LangGraphWorkflowAdapter：后续用于多步骤 Agent、人工审核流和长期状态工作流。

约束：

- Core Domain 不依赖这些框架的数据结构。
- Application Services 通过 Adapter 调用外部框架。
- 引入框架时不得绕过 Chunk、SourceSpan、KnowledgeUnit 和 Feedback 等核心模型。

## 5. 前端架构

### 5.1 页面模块

MVP 页面：

- Dashboard：生命周期控制台。
- Files：文件列表。
- File Detail：文件详情、解析结果、chunk 列表入口。
- Upload：文件上传。
- Chunks：chunk 管理视图。
- Knowledge Units：知识单元列表与详情。
- Wiki Pages：Wiki 列表与详情。
- Search：搜索结果页。
- Chat：知识库问答页。
- Evaluation：反馈和评测样本管理，MVP 可合并到 Dashboard。

### 5.2 前端状态边界

前端只负责：

- 展示服务端状态。
- 收集用户操作。
- 管理局部交互状态。
- 预览文件、chunk、Wiki 和回答引用。

前端不负责：

- 直接解析文件。
- 直接调用 LLM。
- 自行计算知识库指标。
- 自行决定检索上下文。

### 5.3 Chunk 管理界面

Chunk 管理界面应支持：

- 按文件、状态、类型、质量信号筛选。
- 查看 chunk 内容、source span、父子关系。
- 查看原文定位，PDF 至少跳页或文本块。
- 编辑 edited_content。
- 标记 verified、ignored、needs_review。
- 查看关联 Knowledge Unit 和 Wiki。

### 5.4 Wiki 编辑界面

MVP 可以先使用 Markdown 编辑器或 textarea。

功能：

- 查看 Wiki 标题、摘要、正文。
- 查看关联 Knowledge Unit。
- 查看引用来源。
- 编辑内容。
- 重新生成 AI 草稿。
- 标记 draft、verified、archived。

## 6. 核心对象表现形式

本节说明 File、Chunk、Knowledge Unit 和 Wiki 在用户界面与系统内部的表现形式。完整字段定义放在 `docs/04-data-model-spec.md`，本文只定义架构层面的边界。

### 6.1 File

用户界面表现：

- 文件列表项或文件卡片。
- 展示文件名、类型、解析状态、标签、上传时间、chunk 数、知识单元数、Wiki 数。
- 文件详情页展示原文件预览、解析状态、摘要、标签、Document Blocks、Chunks、Knowledge Units 和 Wiki 入口。

系统内部表现：

```json
{
  "id": "file_001",
  "name": "employee-handbook.pdf",
  "type": "pdf",
  "storage_path": "uploads/file_001.pdf",
  "parse_status": "parsed",
  "tags": ["hr", "policy"],
  "summary": "员工手册，包含考勤、请假和报销制度。",
  "created_at": "2026-05-23T00:00:00Z"
}
```

设计要求：

- File 是原始事实来源。
- AI 生成内容不得覆盖原文件。
- MVP 文件删除采用软删除，关联 chunk 默认退出检索和问答，Knowledge Unit、Wiki、citation 保留审计线索并提示来源不可用。
- 后续支持硬删除时，必须处理 chunk、Knowledge Unit、Wiki、citation、对话历史和评估样本的依赖关系。

### 6.2 Chunk

用户界面表现：

- Chunk 是可审阅的证据片段。
- Chunk 列表展示序号、类型、状态、来源位置、字符数、质量信号、父子关系和是否被知识单元引用。
- Chunk 详情展示 raw_content、edited_content、source spans、父 chunk、相邻 chunk、质量信号、关联 Knowledge Unit 和 Wiki。
- 用户可以编辑、忽略、确认、拆分、合并、查看原文位置、生成知识单元。

系统内部表现：

```json
{
  "id": "chunk_023",
  "file_id": "file_001",
  "type": "text",
  "raw_content": "请假申请需提前 1 个工作日提交，并由直属主管审批。",
  "edited_content": "员工请假需至少提前 1 个工作日提交申请，并由直属主管审批。",
  "status": "verified",
  "quality_signals": [],
  "source_spans": [
    {
      "page_number": 3,
      "block_id": "block_012",
      "char_start": 35,
      "char_end": 78,
      "bbox": [82.1, 210.5, 420.3, 228.9]
    }
  ],
  "parent_chunk_id": "chunk_parent_004"
}
```

设计要求：

- Chunk 是“可治理证据片段”，不是最终知识页面。
- Chunk 可以被编辑，但 source_spans 不应被编辑内容覆盖。
- Chunk 必须能回溯到 File、Document Block 或 Timeline Block。
- 已 ignored 的 chunk 默认不参与检索、问答和知识单元生成。

### 6.3 Knowledge Unit

用户界面表现：

- Knowledge Unit 是人工可治理的知识点。
- 列表展示标题、类型、状态、标签、可信等级、来源数量和最近更新时间。
- 详情页展示正文、引用来源、关联 chunk、关联 Wiki、编辑历史和状态操作。
- 用户可以编辑、确认、废弃、添加标签、维护引用来源。

系统内部表现：

```json
{
  "id": "ku_001",
  "title": "请假申请提前时间",
  "type": "rule",
  "content": "员工请假需至少提前 1 个工作日提交申请，并由直属主管审批。",
  "status": "verified",
  "tags": ["hr", "leave"],
  "source_chunk_ids": ["chunk_023"],
  "updated_at": "2026-05-23T00:00:00Z"
}
```

设计要求：

- Knowledge Unit 是 KnowWeave 细粒度知识治理的核心对象。
- verified Knowledge Unit 在问答召回中优先级高于 raw chunk。
- Knowledge Unit 可以来自 chunk、问答记录、Wiki 段落或人工创建。

### 6.4 Wiki Page

用户界面表现：

- Wiki 是面向人阅读的结构化知识页面。
- 页面展示标题、摘要、正文目录、Markdown 内容、关联 Knowledge Unit 和引用来源。
- 用户可以编辑 Wiki、重新生成 AI 草稿、查看引用、标记状态。

系统内部表现：

```json
{
  "id": "wiki_001",
  "title": "员工请假制度",
  "type": "document_wiki",
  "status": "draft",
  "summary": "整理员工请假申请、审批、备案和常见问题。",
  "content_markdown": "## 适用范围\n...\n## 请假申请时间\n员工请假需...",
  "knowledge_unit_ids": ["ku_001", "ku_002"],
  "citations": [
    {
      "file_id": "file_001",
      "chunk_id": "chunk_023",
      "label": "员工手册.pdf 第 3 页"
    }
  ]
}
```

设计要求：

- Wiki 主要给人阅读，也可以作为 AI 的高质量上下文。
- Wiki 的关键结论必须能追溯到 Knowledge Unit、chunk 或人工来源。
- MVP 只要求 Document Wiki，Topic Wiki 和 FAQ Wiki 放在 P1。

### 6.5 对象关系

核心关系：

```text
File
  -> Document Block / Timeline Block
      -> Chunk
          -> Knowledge Unit
              -> Wiki Page
```

使用反馈关系：

```text
Question
  -> Retrieved Chunks / Knowledge Units / Wiki Pages
      -> Answer
          -> Feedback
              -> Evaluation Sample
```

一句话边界：

- File 是原始证据。
- Chunk 是可治理证据片段。
- Knowledge Unit 是已整理的知识点。
- Wiki 是给人阅读、给 AI 复用的知识页面。

## 7. 后端模块划分

### 7.1 API Layer

职责：

- 接收 HTTP 请求。
- 参数校验。
- 调用 Service。
- 返回统一响应。

API 不应直接包含复杂业务逻辑。

建议路由：

```text
/api/files
/api/parsing
/api/chunks
/api/knowledge-units
/api/wiki-pages
/api/search
/api/chat
/api/feedback
/api/evaluation
/api/settings
```

### 7.2 File Service

职责：

- 文件上传。
- 文件元数据管理。
- 文件状态维护。
- 原始文件存储路径管理。
- 重复文件检测。

不负责：

- 解析文件内容。
- 生成 chunk。
- 调用 LLM。

### 7.3 Parsing Service

职责：

- 根据容器类型选择 parser。
- 生成 Document Blocks。
- 生成 Timeline Blocks，占位。
- 生成 asset placeholders。
- 记录解析版本、警告和错误。

MVP Parser：

- txt parser
- markdown parser
- pdf text parser
- docx text parser

预留 Parser：

- table parser
- image parser
- formula parser
- code parser
- media parser

### 7.4 Chunk Service

职责：

- 根据 Document Blocks 或 Timeline Blocks 生成 typed chunks。
- 支持 fixed_size、paragraph、heading、hybrid、parent_child 策略。
- 维护 source spans。
- 维护父子 chunk 关系。
- 计算 chunk 质量信号。
- 支持 chunk 编辑、忽略、确认和重新分块。

不负责：

- 问答生成。
- Wiki 页面生成。

### 7.5 Index Service

职责：

- 维护可检索索引。
- 对文件、chunk、Knowledge Unit、Wiki Page 建立关键词索引。
- 后续支持 embedding 索引。

MVP：

- PostgreSQL full text search。
- 基础 SQL 过滤和排序。

P1：

- pgvector 语义检索。
- hybrid search：全文检索 + 向量检索 + 状态/标签过滤。

### 7.6 Search Service

职责：

- 接收查询。
- 应用过滤条件。
- 调用 Index Service。
- 返回统一 Search Result。
- 支持检索对象：file、chunk、knowledge_unit、wiki_page。
- 支持命中 child chunk 后扩展 parent chunk 上下文。

### 7.7 Knowledge Unit Service

职责：

- 从 chunk 创建候选知识单元。
- 从问答记录创建知识单元。
- 手动创建知识单元。
- 编辑、合并、拆分、废弃知识单元。
- 维护标签、状态、引用来源。

MVP 可先实现：

- 创建。
- 编辑。
- 状态流转。
- 引用维护。

合并和拆分可在 P1 实现。

### 7.8 Wiki Service

职责：

- 生成 Document Wiki。
- 编辑 Wiki 页面。
- 管理 Wiki 状态。
- 关联 Knowledge Unit 和引用来源。

MVP：

- 单文件 Document Wiki。

P1：

- Topic Wiki。
- FAQ Wiki。

### 7.9 Chat Service

职责：

- 接收用户问题。
- 调用 Search Service 获取上下文。
- 组织 prompt。
- 调用 LLM Provider。
- 返回答案和 citation。
- 将模型流式输出转换为统一 SSE 事件。
- 保存问答记录、retrieved_chunks、feedback 入口。

规则：

- 优先召回 verified Knowledge Unit。
- 其次召回 Wiki Page。
- 最后召回 raw chunk。
- 无依据时明确说明无法回答。

SSE 事件协议：

```text
event: delta
data: {"message_id":"msg_001","delta":"员工请假需要"}

event: citations
data: {"message_id":"msg_001","citations":[...]}

event: done
data: {"message_id":"msg_001"}

event: error
data: {"message_id":"msg_001","message":"模型调用失败"}
```

后端规则：

- Chat Service 不应直接透传模型厂商的原始 stream。
- Chat Service 应累积完整 answer_markdown，用于最终保存 ChatMessage。
- citations 应由检索上下文和最终回答共同确定，并在流结束前或结束时发送。
- 如果模型流中断，应发送 error event，并将 ChatMessage 标记为 failed 或 partial。
- 流式输出与最终保存内容必须一致，避免前端看到的答案和数据库保存的答案不一致。

### 7.10 Feedback and Evaluation Service

职责：

- 保存搜索反馈。
- 保存问答反馈。
- 将问答记录标记为评测样本候选。
- 维护 Evaluation Sample。
- 统计基础指标。

MVP：

- 反馈保存。
- 问答记录保存。
- 评测样本候选标记。
- 基础指标统计。

P1：

- 运行评测集。
- 计算 precision、recall、answer_accuracy、citation_precision。

### 7.11 Provider Layer

Provider 抽象：

```text
LLMProvider
EmbeddingProvider
RerankProvider
VisionProvider
OCRProvider
ASRProvider
StorageProvider
```

MVP 实现：

- QwenLLMProvider
- LocalFileStorageProvider

P1 实现：

- QwenEmbeddingProvider
- QwenRerankProvider，可选

占位实现：

- VisionProvider
- OCRProvider
- ASRProvider

兼容实现：

- OpenAICompatibleLLMProvider，可作为 Qwen 兼容调用或后续替换其他模型厂商的适配器。
- OpenAICompatibleEmbeddingProvider，可作为 Qwen 兼容调用或后续替换其他 embedding 厂商的适配器。

## 8. 数据流

### 8.1 文件导入流

```text
Upload File
-> File Service
-> File Storage
-> File Record
-> Parsing Service
-> Document Blocks / Timeline Blocks
-> Chunk Service
-> Typed Chunks
-> Index Service
```

MVP 可以同步处理小文件。解析时间较长时，应记录状态并允许前端轮询。P1/P2 可引入 WebSocket 进行任务状态推送，用于解析、分块、索引、Wiki 生成、评测运行等长任务。

### 8.2 知识沉淀流

```text
Chunk
-> Knowledge Unit Service
-> Draft Knowledge Unit
-> User Review
-> Verified Knowledge Unit
-> Wiki Service
-> Wiki Page
```

### 8.3 问答流

```text
Question
-> Chat Service
-> Search Service
-> Retrieved Context
-> LLM Provider
-> SSE delta events
-> Citations event
-> Done event
-> Chat Record
-> Feedback
```

### 8.4 反馈评估流

```text
Chat Record
-> User Feedback
-> Evaluation Sample Candidate
-> Manual Review
-> Evaluation Dataset
-> Metrics
-> Optimization Task
```

## 9. 数据存储边界

本文不定义完整表结构，但架构上需要以下数据实体：

- File
- ParseResult
- DocumentBlock
- TimelineBlock
- Chunk
- SourceSpan
- KnowledgeUnit
- WikiPage
- Citation
- Tag
- ModelProviderConfig
- ChatSession
- ChatMessage
- RetrievedContext
- Feedback
- EvaluationSample

具体字段在 `docs/04-data-model-spec.md` 中定义。

## 10. 同步与异步任务

### 10.1 MVP 策略

MVP 可采用同步执行 + 状态记录：

- 小文件上传后立即解析。
- 用户触发重新解析时同步执行。
- Wiki 生成和问答同步等待 LLM 返回。

### 10.2 P1 策略

引入后台任务队列：

- parsing job
- chunking job
- indexing job
- wiki generation job
- evaluation job
- task status push，可选 WebSocket

可选技术：

- FastAPI BackgroundTasks
- Celery
- RQ
- Dramatiq

MVP 不强制引入 Celery，避免部署复杂。

## 11. LLM 与 Prompt 边界

LLM 只负责生成候选内容，不直接写入 verified 状态。

LLM 可用于：

- 生成文件摘要。
- 生成候选标签。
- 从 chunk 生成候选 Knowledge Unit。
- 生成 Document Wiki 草稿。
- 基于检索上下文回答问题。
- 从问答记录生成评测样本候选。

LLM 不应：

- 删除原始文件。
- 自动确认知识。
- 在无引用来源时生成确定性知识。
- 绕过 Search Service 自行决定上下文。

流式输出边界：

- LLM Provider 负责适配具体厂商的 stream API。
- Chat Service 负责将 Provider stream 规范化为 KnowWeave SSE 协议。
- API Layer 负责以 `text/event-stream` 返回 SSE。
- 前端只消费 KnowWeave SSE 协议，不感知 Qwen、OpenAI-compatible 或其他模型厂商的原始事件格式。

## 12. DeepParseX 参考边界

DeepParseX 可参考的架构思想：

- 文档上传和管理模块。
- 文档解析、chunk、搜索、问答的业务链路。
- 后端分层思想。
- AI Service 和业务 Service 分离。
- 知识图谱、实体抽取作为后续扩展方向。

KnowWeave 不复用：

- DeepParseX 源代码。
- DeepParseX 数据模型。
- DeepParseX API 路由。
- DeepParseX 前端页面。
- DeepParseX 部署脚本。

KnowWeave 的差异：

- 更小的 MVP 范围。
- 明确引入 LLM Wiki。
- 强调人工知识治理。
- 强调 chunk 可视化编辑和 source span。
- 强调问答反馈沉淀为评测数据集。

## 13. MVP 实现边界

### 13.1 P0 必须实现

- 文件上传和文件列表。
- txt、md、pdf、docx 基础文本解析。
- Document Blocks 基础生成。
- text chunk 生成。
- source span 基础定位。
- chunk 列表、编辑、忽略、确认。
- 关键词搜索。
- Knowledge Unit 创建、编辑、状态管理。
- Document Wiki 生成和编辑。
- 知识库问答和 citation。
- 问答记录、retrieved chunks、feedback 保存。
- 文档索引和基础统计。

### 13.2 P1 尽量实现

- 父子分块可视化。
- Topic Wiki。
- FAQ Wiki。
- Embedding Provider。
- pgvector 语义检索。
- 评测样本管理。
- chunk 质量评分。
- PDF bbox 高亮。

### 13.3 P2 后续扩展

- 表格结构化解析。
- 图片 OCR 和图像描述。
- 公式识别。
- 代码块语言识别。
- 音视频 ASR。
- 多人审核流。
- MinIO。
- 知识图谱。

## 14. 非功能要求

### 14.1 可配置

LLM、Embedding、存储路径、上传大小、分块参数应通过配置管理。

### 14.2 可观察

关键操作应记录状态：

- upload status
- parse status
- chunk status
- wiki generation status
- chat status
- feedback status

### 14.3 可恢复

解析失败、分块失败、Wiki 生成失败时，用户可以查看错误并重试。

### 14.4 可迁移

MVP 使用 PostgreSQL + pgvector 扩展和本地文件系统。MVP 仅启用关系表和全文检索，向量索引与语义检索在 P1 启用。数据模型应避免绑定本地文件系统实现，便于后续迁移到对象存储。

## 15. 后续文档衔接

本架构文档完成后，建议继续产出：

1. `docs/04-data-model-spec.md`
   - 定义 File、Chunk、SourceSpan、KnowledgeUnit、Wiki、Feedback、EvaluationSample 等表结构。

2. `docs/05-ingestion-spec.md`
   - 定义上传、解析、Document Block、Timeline Block、chunking、source span 的接口和流程。

3. `docs/06-llm-wiki-spec.md`
   - 定义 Document Wiki、Topic Wiki、FAQ Wiki 的生成模板和引用规范。

4. `docs/07-search-and-chat-spec.md`
   - 定义检索、上下文组织、问答引用、SSE 事件协议和反馈沉淀。
