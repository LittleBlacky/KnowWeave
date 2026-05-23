# KnowWeave 文档索引

本文档用于说明 `docs` 目录下各规格文档的阅读顺序和职责边界。

## 阅读顺序

1. `01-product-spec.md`
   - 定义 KnowWeave 的产品定位、用户角色、核心概念、MVP 范围和验收标准。
   - 回答“为什么做、为谁做、第一阶段做到什么程度”。

2. `02-knowledge-lifecycle-spec.md`
   - 定义知识从上传、解析、分块、检索、沉淀到评估的完整生命周期。
   - 回答“用户如何对知识处理过程进行细粒度管理，以及系统如何形成闭环”。

3. `03-system-architecture-spec.md`
   - 定义 KnowWeave 的系统架构、模块边界、技术选型、数据流和扩展策略。
   - 回答“前端、后端、存储、AI Provider 和各业务模块如何协作”。

## 文档边界

- 产品规格文档保持高层、稳定，不展开过多技术实现细节。
- 生命周期规格文档负责描述业务过程、用户操作和扩展方向，但不直接定义数据库表结构或 API 字段细节。
- 后续架构、数据模型、API、前端交互和验收用例应继续拆分为独立 Spec。

## 后续计划

建议后续继续补充：

1. `04-data-model-spec.md`：数据模型与表结构。
2. `05-ingestion-spec.md`：文件上传、解析与 chunk 切分实现细节。
3. `06-llm-wiki-spec.md`：Wiki 生成规则、页面结构与引用规范。
4. `07-search-and-chat-spec.md`：搜索、RAG 问答与引用返回格式。
5. `08-frontend-spec.md`：页面、交互、状态和演示流程。
6. `09-acceptance-test-spec.md`：验收用例和演示检查清单。
