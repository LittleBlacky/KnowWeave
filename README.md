# KnowWeave

![KnowWeave Logo](docs/assets/knowweave-logo.png)

面向企业知识文件的 LLM Wiki 知识库管理平台。

KnowWeave 关注的不只是“上传文件后问答”，而是把知识文件经过上传、解析、分块、检索、沉淀、反馈和评估，逐步治理成可追溯、可编辑、可演化的组织知识资产。

## 当前阶段

项目当前处于 Spec Coding 阶段，已沉淀产品、生命周期、架构、数据模型、ingestion、LLM Wiki、搜索与问答、前端交互、验收测试和评测闭环规格文档。代码实现应以后续工程实现 Spec 为准，不直接照搬参考项目代码。

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

## MVP 边界

MVP 优先完成：

- txt、md、pdf、docx 文件上传与基础解析。
- Document Block、text chunk、source span。
- chunk 查看、编辑、忽略、确认和原文定位。
- Knowledge Unit 管理。
- Document Wiki 生成。
- 关键词搜索、AI 问答、citation、问答记录和 retrieved_contexts。

P1/P2 再逐步扩展向量检索、模型配置页面、Wiki Revision 对比回滚、表格/图片/公式/代码深度解析和音视频解析。
