# KnowWeave P1: LLM 主动知识策展

**Branch**: `002-knowweave-p1` | **Date**: 2026-06-15 | **依赖**: P0 完成

## 一句话定位

P1 将 KnowWeave 从「被动知识工具」升级为「主动知识策展平台」——LLM 不只是等人来问，而是定期从文件、chunk、问答、反馈中自主发现高价值知识，沉淀为 Topic Wiki、FAQ Wiki 和知识摘要。

## P1 核心差异

| | P0 | P1 |
|---|---|---|
| 搜索 | 关键词 | 语义向量 + hybrid |
| Wiki | Document Wiki | Topic Wiki + FAQ Wiki |
| 知识治理 | 手动操作 | 自动发现 + 建议 |
| LLM 角色 | 被动回答 | 主动策展 |
| 评测 | 候选样本 | 评测集 + 运行 + 指标 |
| 任务 | 同步 API | 异步 Worker |

## Sprint 划分

### Sprint 1: 基础设施升级（预计 6 个任务）

**目标**：语义搜索上线，Wiki 可追溯版本，长任务不阻塞。

- T101 启用 pgvector embedding 字段与向量索引
- T102 实现 Embedding Provider 接口与 Fake Embedding
- T103 实现语义搜索 + hybrid search（关键词 + 向量融合）
- T104 创建 wiki_revisions 表与迁移
- T105 实现 Wiki Revision 保存/列表/回滚
- T106 前端 Wiki 编辑增强（Markdown 预览、引用插入）

### Sprint 2: 高级 Wiki（预计 6 个任务）

**目标**：Topic Wiki 和 FAQ Wiki 上线，知识可跨文件聚合。

- T107 实现 Topic Wiki 生成（用户选主题 + 多文件/KU）
- T108 实现 FAQ Wiki 生成（从文件内容 + 问答记录）
- T109 Wiki 内链与反链基础能力
- T110 前端 Topic Wiki 创建与编辑页面
- T111 前端 FAQ Wiki 管理页面
- T112 Document Wiki 模板优化（规则/流程/术语/风险分段）

### Sprint 3: LLM 主动知识策展（核心亮点，预计 8 个任务）

**目标**：LLM 定期自动扫描知识库，发现高价值知识并组织。

- T113 实现知识质量评分算法（chunk 引用频率、反馈信号、时效性）
- T114 实现 LLM 策展触发器（定时 / 事件驱动）
- T115 实现「知识发现报告」生成（LLM 扫描后输出：哪些知识值得沉淀、哪些已过时、哪些需要合并）
- T116 实现自动 Topic Wiki 建议（LLM 发现跨文件主题，建议创建 Topic Wiki）
- T117 实现自动 FAQ 发现（从 Chat 历史中提取高频问题，建议沉淀为 FAQ）
- T118 实现知识新鲜度检查（标记可能过时的 chunk/KU/Wiki）
- T119 前端策展仪表盘（展示 LLM 发现报告、建议操作）
- T120 前端知识健康看板（新鲜度、引用率、反馈质量可视化）

### Sprint 4: 知识治理 + 评测闭环（预计 6 个任务）

**目标**：知识单元可合并拆分，评测集可正式运行。

- T121 实现 Knowledge Unit 合并（多选 KU → 合并为一个）
- T122 实现 Knowledge Unit 拆分（长 KU → 拆为多个子 KU）
- T123 实现 evaluation_runs 与指标计算（Recall@K, Precision@K, Citation Precision）
- T124 前端 KU 合并/拆分交互
- T125 前端评测运行页面
- T126 端到端 P1 smoke 脚本

## 与 Yuxi 的差异定位

| 维度 | Yuxi | KnowWeave P1 |
|---|---|---|
| 智能体 | LangGraph 多智能体 | 不引入（P2 考虑） |
| 知识图谱 | Neo4j + Milvus 图谱 | pgvector 向量关系（轻量） |
| 核心差异 | Agent + Skills + 沙盒 | **LLM 主动策展 + Wiki 沉淀** |
| 文档解析 | MinerU/PaddleX/RapidOCR | pdfplumber + 后续可扩展 |
| 多租户 | 是 | 否（单用户模式） |

KnowWeave 不做 Yuxi 的翻版。核心差异是 **LLM Wiki 的主动性**——不是等用户来组织知识，而是 LLM 定期自己去发现、整理、建议。

## 技术约束

- 继续使用 FastAPI + PostgreSQL/pgvector + Next.js
- Embedding 默认用 Fake Provider，真实模型通过环境变量配置
- 异步任务使用 Python 后台线程（不引入 Celery/Redis for P1）
- 数据仍以 PostgreSQL 为主，不引入 Milvus/Neo4j
