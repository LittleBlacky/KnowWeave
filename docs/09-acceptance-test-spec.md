# KnowWeave 验收测试规格说明书

版本：v0.2
更新时间：2026-05-24
状态：草案
关联文档：

- `docs/01-product-spec.md`
- `docs/02-knowledge-lifecycle-spec.md`
- `docs/03-system-architecture-spec.md`
- `docs/04-data-model-spec.md`
- `docs/05-ingestion-spec.md`
- `docs/06-llm-wiki-spec.md`
- `docs/07-search-and-chat-spec.md`
- `docs/08-frontend-spec.md`

## 1. 文档目标

本文定义 KnowWeave 的 P0 MVP 验收测试、演示流程、检查清单和失败处理口径。

验收测试的目标不是证明系统已经具备企业级完整能力，而是证明 P0 主链路真实闭环：

```text
上传文件 -> 解析 -> Document Block -> Chunk -> 人工治理 -> Search -> Chat -> Citation -> Wiki -> Feedback -> Evaluation Sample Candidate
```

验收必须回答：

- P0 做到了什么。
- 哪些能力只是预留，不作为 P0 验收失败。
- 演示时应该准备哪些数据。
- 每个模块如何判断通过。
- 如果失败，如何判断是阻塞问题、可接受降级还是 P1/P2 范围。

## 2. 验收边界

### 2.1 P0 验收必须覆盖

| 范围 | 必须覆盖 |
| --- | --- |
| 文件 | txt、md、pdf、docx 至少各有一类可进入系统；演示至少包含 Markdown 和 PDF |
| 解析 | 生成 parse result、document blocks、错误信息和重试入口 |
| 分块 | 生成 text chunk、source span、quality flags、curation status |
| 人工治理 | 查看、编辑、忽略、确认 chunk |
| 原文定位 | chunk/citation 至少能定位到文件、页码/行号/document_block |
| Wiki | 单文件 Document Wiki 生成、编辑、状态流转、引用 |
| Search | 关键词搜索 file、chunk、Knowledge Unit、Wiki |
| Chat | SSE 流式回答、retrieved contexts、citations |
| Feedback | answer/citation/chunk/wiki 反馈可以保存 |
| 评估沉淀 | 反馈可以形成 evaluation sample candidate |

### 2.2 P0 不作为失败项

| 能力 | 原因 | 后续阶段 |
| --- | --- | --- |
| pgvector 语义检索质量调优 | MVP 只要求 PostgreSQL + pgvector 基线和关键词检索闭环 | P1 |
| Wiki Revision diff/rollback | MVP 预留，P1 启用完整版本对比 | P1 |
| Topic Wiki / FAQ Wiki | MVP 只要求 Document Wiki | P1 |
| PDF bbox 精确高亮 | MVP 只要求页码、block 或文本范围定位 | P1 |
| Web 模型配置页面 | MVP 可用环境变量配置 Qwen 默认 Provider | P1 |
| 表格/图片/公式/代码深度解析 | MVP 只要求 typed block/chunk 扩展点 | P2 |
| 音视频转写和时间轴定位 | MVP 只预留 timeline/source span 字段 | P2 |
| 多人协作、权限和评论 | MVP 可单用户模式 | P2 |

## 3. 验收角色

| 角色 | 职责 |
| --- | --- |
| 演示操作者 | 按演示脚本完成端到端流程 |
| 产品验收人 | 判断流程是否满足业务目标 |
| 技术验收人 | 判断数据、API、状态和错误处理是否满足 Spec |
| 领域专家 | 判断 Wiki 和回答是否有基本可信度 |
| 记录人 | 记录通过项、失败项、降级项和后续任务 |

## 4. 验收环境

### 4.1 环境要求

| 项目 | P0 要求 |
| --- | --- |
| 部署方式 | 本地或单机部署即可 |
| 数据库 | PostgreSQL，安装 pgvector 扩展 |
| 文件存储 | 本地文件系统即可 |
| LLM Provider | Qwen 默认 Provider 可用 |
| Embedding | 可不启用；如果启用，结果不作为 P0 关键验收 |
| 浏览器 | Chrome 或 Edge 最新稳定版 |
| 网络 | 能访问 Qwen API 或演示替身服务 |

### 4.2 配置检查

验收开始前必须确认：

- 后端服务可启动。
- 前端服务可启动。
- 数据库连接成功。
- migration 已执行。
- Qwen API Key 或模型配置有效。
- 文件上传目录可写。
- 日志目录可写。
- 测试数据目录存在。

## 5. 演示数据准备

### 5.1 最小数据集

| 文件 | 类型 | 内容要求 | 用途 |
| --- | --- | --- | --- |
| `company_policy.md` | Markdown | 有标题、列表、表格、多个段落 | 验证 Markdown 解析、行号定位和 Wiki |
| `security_handbook.pdf` | PDF | 至少 3 页，有明确标题和段落 | 验证 PDF 页码定位和 citation |
| `team_faq.docx` | DOCX | 有问答式内容和多级标题 | 验证 DOCX block 和 chunk |
| `notes.txt` | TXT | 简单纯文本 | 验证基础文本主链路 |

### 5.2 推荐内容主题

演示文件内容应围绕同一业务主题，便于搜索和问答形成可验证结果。例如：

- 信息安全制度。
- 员工报销规范。
- 系统权限申请流程。
- AI 知识库运营说明。

### 5.3 数据质量要求

| 要求 | 说明 |
| --- | --- |
| 可搜索关键词 | 每个文件至少包含 3 个明确关键词 |
| 可问答问题 | 至少准备 5 个有标准答案的问题 |
| 可定位证据 | 每个标准答案至少对应 1 个来源段落或页码 |
| 可制造反馈 | 至少准备 1 个引用错误或答案不完整的反馈案例 |
| 可制造低质量 chunk | 至少有页眉、目录、短句或重复段落，用于低质量提示 |

## 6. P0 演示主剧本

### 6.1 剧本总览

```mermaid
flowchart LR
  Prep["准备演示数据"] --> Upload["上传文件"]
  Upload --> Parse["解析文件"]
  Parse --> Blocks["查看 Document Blocks"]
  Blocks --> Chunk["查看/编辑 Chunk"]
  Chunk --> Source["定位原文"]
  Source --> Wiki["生成 Document Wiki"]
  Wiki --> Search["搜索知识"]
  Search --> Chat["流式问答"]
  Chat --> Citation["查看 Citation"]
  Citation --> Feedback["提交反馈"]
  Feedback --> Eval["沉淀评测样本候选"]
```

### 6.2 演示步骤

| 步骤 | 操作 | 通过信号 |
| --- | --- | --- |
| 1 | 打开 Dashboard | 能看到文件、chunk、Wiki、反馈等统计入口 |
| 2 | 上传 Markdown 和 PDF | 文件列表出现记录，状态为 uploaded 或 pending |
| 3 | 触发解析 | 状态进入 parsing，完成后为 parsed 或 chunked |
| 4 | 查看 Document Blocks | blocks 有顺序、类型、预览和定位字段 |
| 5 | 查看 chunk 列表 | chunks 有内容、source span、status、quality flags |
| 6 | 编辑一个 chunk | raw_content 保持只读，edited_content 保存成功 |
| 7 | 标记一个 chunk 为 ignored | ignored chunk 默认不进入搜索和问答 |
| 8 | 打开 Source Viewer | Markdown 能跳行号；PDF 至少能跳页码或展示页码 |
| 9 | 生成 Document Wiki | Wiki 有标题、Markdown 正文、citation、draft 状态 |
| 10 | 编辑 Wiki 并填写 change_summary | 保存成功，状态符合流转规则 |
| 11 | 搜索关键词 | 返回 file、chunk、KU 或 Wiki 结果 |
| 12 | 发起 Chat 问答 | SSE 增量展示回答 |
| 13 | 查看 retrieved contexts | 能看到 retrieval_run_id 和召回对象 |
| 14 | 点击 citation | citation 能定位到 chunk 或 source span |
| 15 | 提交 citation_wrong 或 answer_wrong | feedback 保存成功 |
| 16 | 勾选沉淀评测样本候选 | evaluation sample candidate 记录成功 |

## 7. 模块验收

### 7.1 文件管理

| 编号 | 验收项 | 优先级 | 通过标准 |
| --- | --- | --- | --- |
| FILE-001 | 上传支持 txt/md/pdf/docx | P0 | 支持类型可成功入库，不支持类型有明确错误 |
| FILE-002 | 文件列表展示元数据 | P0 | 文件名、类型、上传时间、解析状态可见 |
| FILE-003 | 文件软删除 | P0 | 删除后默认列表隐藏，关联引用保留审计线索 |
| FILE-004 | 重复文件提示 | P1 | sha256 或文件名疑似重复时提示用户 |

### 7.2 Ingestion 与解析

| 编号 | 验收项 | 优先级 | 通过标准 |
| --- | --- | --- | --- |
| ING-001 | 解析状态流转 | P0 | uploaded -> parsing -> parsed/chunked 或 failed |
| ING-002 | 解析失败可见 | P0 | failed 状态展示错误码和可读原因 |
| ING-003 | Document Block 有序 | P0 | block_index 从 0 递增，顺序稳定 |
| ING-004 | typed block 预留 | P0 | 表格/图片/公式/代码无法深度解析时不直接丢弃 |
| ING-005 | 重新解析 | P1 | 可触发重新解析并记录新 parse result |

### 7.3 Chunking 与治理

| 编号 | 验收项 | 优先级 | 通过标准 |
| --- | --- | --- | --- |
| CHK-001 | 生成 text chunk | P0 | chunk 有 raw_content、chunk_index、source span |
| CHK-002 | source span 写入 | P0 | PDF 至少 page_number 或 document_block_id；Markdown 至少 line_start/line_end |
| CHK-003 | 编辑 chunk | P0 | edited_content 保存后优先用于预览和搜索上下文 |
| CHK-004 | raw_content 只读 | P0 | 编辑不会覆盖原始内容 |
| CHK-005 | 忽略 chunk | P0 | ignored chunk 默认不参与搜索、问答和 Wiki 生成 |
| CHK-006 | 确认 chunk | P0 | chunk_status 可变为 verified |
| CHK-007 | 低质量提示 | P0 | too_short、too_long、missing_source_span 等 flags 可展示 |
| CHK-008 | 父子分块展示 | P1 | parent_chunk_id 可视化展示或调试可见 |

### 7.4 Source Viewer

| 编号 | 验收项 | 优先级 | 通过标准 |
| --- | --- | --- | --- |
| SRC-001 | Markdown 定位 | P0 | 可展示行号或跳转到对应文本范围 |
| SRC-002 | PDF 定位 | P0 | 至少可跳到页码或展示页码和文本 preview |
| SRC-003 | DOCX 定位 | P0 | 至少可定位到 document_block 或段落索引 |
| SRC-004 | edited_content 提示 | P0 | 编辑内容与原文不同，应提示定位仍回 raw_content |
| SRC-005 | source unavailable | P0 | 来源不可用时按钮 disabled，保留 citation 快照 |
| SRC-006 | bbox 高亮 | P1 | PDF.js 或 react-pdf 支持区域高亮 |

### 7.5 Knowledge Unit

| 编号 | 验收项 | 优先级 | 通过标准 |
| --- | --- | --- | --- |
| KU-001 | 候选 KU 生成或创建 | P0 | 可从 chunk 生成或手动创建 KU |
| KU-002 | KU 来源可追溯 | P0 | KU 至少关联一个 source chunk |
| KU-003 | KU 状态流转 | P0 | draft、verified、archived 可用 |
| KU-004 | KU 编辑 | P0 | title、summary 可编辑 |
| KU-005 | KU 合并拆分 | P1 | 可合并重复 KU 或拆分过大 KU |

### 7.6 LLM Wiki

| 编号 | 验收项 | 优先级 | 通过标准 |
| --- | --- | --- | --- |
| WIKI-001 | Document Wiki 生成 | P0 | 单文件可生成 Wiki 草稿 |
| WIKI-002 | Markdown 正文 | P0 | Wiki 正文以 Markdown 保存和展示 |
| WIKI-003 | citation 强制展示 | P0 | 关键结论至少有 citation 或人工来源说明 |
| WIKI-004 | Wiki 编辑 | P0 | 保存需 change_summary |
| WIKI-005 | 状态流转 | P0 | draft、pending_review、verified、archived 可用 |
| WIKI-006 | source_available 展示 | P0 | 来源失效时 Wiki 可读但引用提示不可用 |
| WIKI-007 | Revision diff/rollback | P1 | 可查看历史版本并回滚 |

### 7.7 Search

| 编号 | 验收项 | 优先级 | 通过标准 |
| --- | --- | --- | --- |
| SRCH-001 | 关键词搜索 | P0 | 中文关键词可基础匹配 |
| SRCH-002 | 多对象结果 | P0 | 可返回 file、chunk、KU、Wiki |
| SRCH-003 | 过滤 source_available | P0 | 不可用来源可过滤或标识 |
| SRCH-004 | ignored chunk 过滤 | P0 | 默认不返回 ignored/archived chunk |
| SRCH-005 | retrieval_run_id | P0 | 每次搜索或 Chat 召回有 run id |
| SRCH-006 | score_breakdown 预留 | P1 | 可解释混合检索分数 |

### 7.8 Chat 与 RAG

| 编号 | 验收项 | 优先级 | 通过标准 |
| --- | --- | --- | --- |
| CHAT-001 | 提问入口 | P0 | 用户可输入问题并发送 |
| CHAT-002 | SSE 流式回答 | P0 | start、delta、citations、done 或 error 能被前端处理 |
| CHAT-003 | retrieved contexts | P0 | 可查看本轮召回对象和 retrieval_run_id |
| CHAT-004 | citation 展示 | P0 | 回答后展示 citation panel |
| CHAT-005 | citation 定位 | P0 | 点击 citation 可打开 Source Viewer |
| CHAT-006 | 最终答案一致 | P0 | 前端最终展示与数据库保存 content_markdown 一致 |
| CHAT-007 | Provider 错误处理 | P0 | LLM 调用失败有错误提示和重试 |

### 7.9 Feedback 与评估样本候选

| 编号 | 验收项 | 优先级 | 通过标准 |
| --- | --- | --- | --- |
| FB-001 | answer feedback | P0 | answer_helpful/answer_wrong 可保存 |
| FB-002 | citation feedback | P0 | citation_helpful/citation_wrong 可保存 |
| FB-003 | chunk feedback | P0 | chunk_low_quality 可保存并影响 quality flags |
| FB-004 | wiki feedback | P0 | wiki_needs_update 可保存 |
| FB-005 | evaluation candidate | P0 | 可从反馈沉淀候选评测样本 |
| FB-006 | retrieval_run_id 关联 | P0 | 来自 Search/Chat 的反馈保留 run id |

### 7.10 前端交互

| 编号 | 验收项 | 优先级 | 通过标准 |
| --- | --- | --- | --- |
| UI-001 | Dashboard | P0 | 能看到关键统计和待处理列表 |
| UI-002 | Files | P0 | 文件上传、列表、详情、解析入口可用 |
| UI-003 | Chunks | P0 | chunk 列表、详情、编辑、定位可用 |
| UI-004 | Wiki | P0 | Wiki 列表、详情、编辑、citation panel 可用 |
| UI-005 | Search | P0 | 搜索输入、筛选、结果分组可用 |
| UI-006 | Chat | P0 | 流式回答、citation panel、feedback 可用 |
| UI-007 | Markdown 安全渲染 | P0 | 禁止原始 HTML，使用 sanitize |
| UI-008 | 移动端适配 | P2 | 非 P0 验收项 |

## 8. 数据验收

### 8.1 核心对象落库

P0 验收时至少应能看到以下对象：

| 对象 | 最小数量 | 说明 |
| --- | ---: | --- |
| knowledge_files | 4 | txt、md、pdf、docx |
| parse_results | >= 2 | 至少 Markdown 和 PDF 解析成功 |
| document_blocks | >= 5 | 来自至少 2 个文件 |
| chunks | >= 10 | 至少有 source span |
| source_spans | >= chunks 数 | 每个 P0 chunk 至少一个 |
| knowledge_units | >= 1 | 可自动或手动生成 |
| wiki_pages | >= 1 | Document Wiki |
| distinct retrieval_run_id | >= 2 | Search 和 Chat 各至少一次；P0 不要求单独 `retrieval_runs` 表 |
| retrieved_contexts | >= 1 | Chat 召回上下文 |
| citations | >= 1 | Wiki 或 Chat citation |
| feedback | >= 1 | 用户反馈 |
| evaluation_samples | >= 1 candidate | 候选评测样本 |

### 8.2 数据一致性检查

| 检查项 | 通过标准 |
| --- | --- |
| chunk -> file | 每个 chunk 能回到 source file |
| chunk -> source span | P0 chunk 不应缺 source span |
| citation -> source | citation 至少有 chunk、KU、Wiki 或人工来源之一 |
| retrieved_contexts -> retrieval_run_id | retrieved_contexts 必须有 retrieval_run_id；P0 不要求单独 `retrieval_runs` 表 |
| feedback -> target | feedback target_type 和 target_id 可解析 |
| soft delete | 文件软删除后新问答默认不召回其 chunk |

## 9. API 验收

本节只定义验收口径，具体路由以工程实现为准。

| 能力 | 必须有 API 或等价操作 |
| --- | --- |
| 文件上传 | 是 |
| 文件列表和详情 | 是 |
| 触发解析 | 是 |
| 查看 parse result 和 blocks | 是 |
| 查看 chunk 列表和详情 | 是 |
| 更新 chunk edited_content/status | 是 |
| 生成 Document Wiki | 是 |
| 更新 Wiki 内容和状态 | 是 |
| Search | 是 |
| Chat streaming | 是 |
| 查看 citations | 是 |
| 提交 feedback | 是 |
| 创建 evaluation sample candidate | 是 |

API 验收关注：

- 请求参数可校验。
- 错误响应有错误码和可读信息。
- 长任务有状态可查。
- 不返回 API Key。
- 关键写操作记录 updated_at。

## 10. 非功能验收

| 类别 | P0 要求 |
| --- | --- |
| 响应时间 | 普通搜索 3 秒内返回；普通 Chat 30 秒内开始或完成可见输出 |
| 稳定性 | 演示主链路连续跑通 2 次 |
| 数据安全 | 不在前端暴露 LLM API Key |
| 可追溯 | Wiki、Chat、KU、citation 可回到来源 |
| 可维护 | README 能说明启动、配置和演示流程 |
| 错误处理 | 上传、解析、LLM、检索失败均有明确提示 |
| 可观测 | 后端日志能定位请求、任务和错误 |

## 11. 演示检查清单

### 11.1 演示前

- 数据库已初始化。
- 演示文件已准备。
- 服务已启动。
- Qwen 配置可用。
- 浏览器可访问前端。
- 旧演示数据已清理或标记。
- 网络状态稳定。
- 备用问题和备用文件已准备。

### 11.2 演示中

- 不跳过上传和解析。
- 明确展示 chunk 来源定位。
- 至少展示一次 chunk 编辑。
- 至少展示一次 ignored chunk 的效果或状态。
- 至少生成一个 Document Wiki。
- 至少发起一次 Chat。
- 至少点击一次 citation。
- 至少提交一次 feedback。
- 至少展示一次 evaluation sample candidate。

### 11.3 演示后

- 记录通过项。
- 记录失败项。
- 标记失败等级。
- 记录可接受降级。
- 记录 P1/P2 延后项。
- 更新任务表或 issue。

## 12. 失败分级

| 等级 | 定义 | 示例 | 处理 |
| --- | --- | --- | --- |
| Blocker | P0 主链路无法继续 | 文件不能上传；Chat 完全不可用 | 必须修复后再验收 |
| Major | 核心能力可用但关键证据缺失 | citation 无法定位；chunk 无 source span | 原则上需修复 |
| Minor | 不影响主链路的体验或展示问题 | 表格列宽不佳；文案不清晰 | 可记录后续修复 |
| Deferred | 明确属于 P1/P2 | bbox 高亮、向量调优 | 不阻塞 P0 |

## 13. 验收矩阵

| 主链路 | P0 必须过 | P1 可选 | P2 不验收 |
| --- | --- | --- | --- |
| 上传文件 | 是 | 批量上传 | 外部知识源同步 |
| 解析文件 | 是 | 异步任务队列 | 多媒体解析 |
| 生成 chunk | 是 | 手动拆分/合并 | 多模态深度 chunk |
| 原文定位 | 是 | bbox 高亮 | 词级高亮 |
| 生成 Wiki | 是 | Topic/FAQ Wiki | Knowledge Network Page |
| 搜索 | 是 | pgvector/hybrid | 图谱检索 |
| Chat | 是 | Prompt 版本管理 | 多 Agent 协作问答 |
| Feedback | 是 | 自动修复建议 | 自动闭环治理 |
| Evaluation | 候选样本 | evaluation_runs | 自动回归评估平台 |

## 14. 验收报告模板

```markdown
# KnowWeave P0 验收报告

日期：
版本/Commit：
验收环境：
参与人：

## 总体结论

- 通过 / 有条件通过 / 不通过

## 主链路结果

| 环节 | 结果 | 证据 | 问题 |
| --- | --- | --- | --- |
| 文件上传 |  |  |  |
| 解析 |  |  |  |
| chunk 治理 |  |  |  |
| 原文定位 |  |  |  |
| Wiki |  |  |  |
| Search |  |  |  |
| Chat |  |  |  |
| Feedback |  |  |  |
| Evaluation Candidate |  |  |  |

## 阻塞问题

## 可接受降级

## P1/P2 延后项

## 后续任务
```

## 15. 与其他 Spec 的对齐

| 来源文档 | 本文承接方式 |
| --- | --- |
| `01-product-spec.md` | 承接 MVP 范围、用户角色、功能验收和演示目标 |
| `02-knowledge-lifecycle-spec.md` | 承接上传、解析、分块、检索、沉淀、评估的生命周期验收 |
| `03-system-architecture-spec.md` | 承接模块边界、Provider、SSE、WebSocket 和部署验收 |
| `04-data-model-spec.md` | 承接核心对象、关系、source span、retrieval_run_id 和 soft delete 数据验收 |
| `05-ingestion-spec.md` | 承接文件解析、Document Block、chunking、source span 和重新处理验收 |
| `06-llm-wiki-spec.md` | 承接 Document Wiki、citation、状态流转和 revision 预留验收 |
| `07-search-and-chat-spec.md` | 承接 Search Result、Chat SSE、citations、feedback 和 evaluation sample candidate |
| `08-frontend-spec.md` | 承接页面、Source Viewer、流式 Markdown、citation panel 和 feedback UI |

## 16. 后续 Spec

评测规格已拆分完成：

1. `10-evaluation-spec.md`
   - 定义 evaluation datasets、evaluation_runs、指标计算、失败样本分析和回归评估。
   - 将本文中的 evaluation sample candidate 验收进一步细化为可运行的评测体系。

工程实现规格已完成：

1. `11-backend-implementation-spec.md`
   - 将本文验收项落到 API、数据库、服务层和自动化测试。
2. `12-frontend-implementation-spec.md`
   - 将本文验收场景落到页面、组件、交互状态和端到端测试。
3. `13-devops-and-demo-spec.md`
   - 将本文演示剧本落到本地启动、演示数据和 smoke 脚本。

下一步进入工程骨架实现，并把本文检查清单转换为 P0 smoke 和演示前检查脚本。
