# KnowWeave 知识生命周期细粒度管理规格说明书

版本：v1.0
日期：2026-05-23  
状态：草案  
关联文档：`docs/01-product-spec.md`

## 1. 文档目标

本文定义 KnowWeave 中“知识从文件进入系统，到被检索、沉淀、评估和持续维护”的完整生命周期。与普通文档问答系统不同，KnowWeave 不把上传、解析、分块、检索、沉淀和评估视为黑盒流程，而是将每个阶段拆成用户可观察、可干预、可回滚、可评估的细粒度操作。

该能力是 KnowWeave 的核心产品差异：

- AI 负责自动化处理和生成候选结果。
- 用户负责审查、修正、组织和确认知识。
- 系统负责记录每一步处理结果、状态和来源。

## 2. 文档边界

本文关注知识生命周期的产品行为和扩展设计，不直接定义数据库表结构、后端 API 路由、前端组件结构或具体模型调用参数。

本文与其他文档的关系：

- `01-product-spec.md` 定义产品目标和 MVP 边界。
- 本文定义知识处理过程中的用户操作、系统状态、扩展点和验收场景。
- 后续数据模型 Spec 应将本文中的 File、Document Block、Timeline Block、Chunk、Knowledge Unit、Wiki、Feedback、Evaluation Sample 转换为具体表结构。
- 后续架构 Spec 应将本文中的 parser、chunker、retriever、curator、evaluator 转换为模块边界。

## 3. 设计原则

### 3.1 全流程可见

用户应能看到每个文件当前处于哪个阶段：已上传、待解析、解析中、解析失败、已分块、已索引、已生成知识单元、已沉淀为 Wiki、已评估。

### 3.2 每一步可干预

用户不只能点击“一键处理”，也可以在关键节点修改处理策略，例如重新选择解析器、调整分块参数、删除低质量 chunk、确认知识单元、重新生成 Wiki。

### 3.3 AI 输出默认不可信

AI 生成的摘要、标签、知识单元、Wiki 页面和问答评价默认是候选结果。只有经过用户确认后，才进入可信知识集合。

### 3.4 原始文件永远是事实源

系统可以生成 chunk、知识单元、Wiki 页面和问答答案，但所有衍生知识都必须能追溯到原始文件或人工补充来源。

### 3.5 支持渐进增强

MVP 可以先实现手动操作和基础规则，后续再逐步加入异步任务、向量检索、自动评估和批量治理。

## 4. 生命周期总览

KnowWeave 的知识生命周期分为六个阶段：

1. 知识上传：将原始文件纳入知识库。
2. 内容解析：从文件中提取可处理文本、结构和嵌入内容。
3. 内容分块：将文档块或时间轴片段转换为可检索、可引用、可治理的 chunk。
4. 知识检索：基于文件、chunk、知识单元和 Wiki 页面进行召回。
5. 知识沉淀：将临时检索结果和 AI 生成内容沉淀为知识单元和 Wiki。
6. 知识评估：评估解析质量、分块质量、检索质量、Wiki 质量和问答质量。

推荐主流程：

```text
Ingestion Loop:
File -> Document Blocks / Timeline Blocks -> Typed Chunks -> Index -> Knowledge Unit -> Wiki Page

Usage Feedback Loop:
Question -> Retrieved Chunks -> Answer -> Feedback -> Evaluation Sample -> Metric -> Optimization Task -> Knowledge Curation
```

其中，Knowledge Unit 和 Wiki Page 既可以在首次导入后由 chunk 生成，也可以在用户问答和反馈后继续沉淀更新。KnowWeave 的核心不是单向流水线，而是导入治理与使用反馈共同驱动的闭环。

RAG 与 Wiki 在生命周期中的定位：

- RAG 位于“知识检索”和“知识消费”环节，负责围绕一次用户问题召回证据并生成即时回答。
- Wiki 位于“知识沉淀”和“知识维护”环节，负责把文件、chunk、知识单元、问答反馈和人工修订沉淀为长期可维护页面。
- RAG 可以召回 Wiki 页面作为高质量上下文。
- 高质量 RAG 问答和用户反馈可以反向生成 Knowledge Unit、FAQ Wiki 或 Topic Wiki。
- RAG 回答不自动成为可信 Wiki；必须经过来源校验、人工确认或规则化沉淀流程。

Wiki 的来源路径：

```text
Document Wiki:
File -> Document Blocks -> Chunks -> Knowledge Units(optional) -> Document Wiki

Topic Wiki:
Search Results / Selected Files / Knowledge Units -> Topic Wiki

FAQ Wiki:
Chat Records -> Feedback -> Evaluation Samples -> FAQ Knowledge Units -> FAQ Wiki
```

MVP 只要求 Document Wiki。Topic Wiki、FAQ Wiki 和从问答记录自动沉淀 Wiki 放在 P1。

### 4.1 多类型内容扩展点

MVP 阶段以文本知识处理为主，但生命周期设计必须为图、表格、公式、代码块、音视频转写等非纯文本内容预留扩展位置。系统不应把所有内容都强行压平成普通文本 chunk，而应允许后续引入多类型内容对象。

预留的内容类型：

- text：普通文本段落。
- table：表格、Excel sheet、Markdown 表格。
- image：图片、截图、扫描页、图表。
- formula：数学公式、科学公式、工程计算表达式。
- code：代码片段、配置片段、命令示例。
- transcript：音视频转写文本。
- mixed：同时包含文本、图、表或公式的复合片段。

MVP 不要求完整实现这些类型，但数据模型、处理流程和页面交互需要避免只绑定 `text` 单一类型。

### 4.2 容器文档与嵌入内容

KnowWeave 需要区分“文件容器类型”和“内容块类型”。PDF、Markdown、DOCX、PPTX、HTML 等通常不是单一内容类型，而是复合容器，内部可能同时包含文本、表格、图片、图表、公式、代码块和附件。

示例：

```text
PDF file
  -> text block
  -> table block
  -> image block
  -> formula block

Markdown file
  -> heading block
  -> paragraph block
  -> table block
  -> code block
  -> formula block
  -> image reference

DOCX file
  -> paragraph block
  -> table block
  -> embedded image
  -> equation object
```

因此，解析流程不应只根据文件后缀决定 chunk 类型。正确流程应是：

```text
Container Parser -> Document Block Detection -> Asset Extraction -> Typed Chunk Generation
```

其中：

- Container Parser 负责打开 PDF、Markdown、DOCX 等容器文件。
- Document Block Detection 负责识别内部 block 类型和顺序。
- Asset Extraction 负责提取图片、表格、公式等嵌入对象或占位记录。
- Typed Chunk Generation 负责将 block 转换为 text、table、image、formula、code、mixed 等 chunk。

MVP 中可以只深度处理 text block，但必须保留其他 block 的位置、类型和上下文，避免后续扩展时无法回溯。

### 4.3 媒体容器与时间轴内容

音视频文件需要按“时间轴容器”处理。它们通常不包含传统段落结构，而是由音轨、视频轨、字幕、关键帧、屏幕文字、章节和说话人片段组成。

示例：

```text
Audio file
  -> audio track
  -> transcript segment
  -> speaker turn
  -> timestamp citation

Video file
  -> audio track
  -> video frames
  -> transcript segment
  -> keyframe
  -> screen OCR text
  -> chapter segment
```

推荐流程：

```text
Media Parser -> Track Extraction -> ASR/OCR/Keyframe Detection -> Timeline Blocks -> Typed Chunks
```

其中：

- Media Parser 负责读取 mp3、wav、mp4、mov 等媒体容器。
- Track Extraction 负责抽取音轨、视频轨、字幕轨和元数据。
- ASR/OCR/Keyframe Detection 负责生成转写文本、屏幕文字和关键帧。
- Timeline Blocks 负责按时间戳组织内容。
- Typed Chunks 负责生成 transcript、image、mixed 等 chunk。

MVP 不需要实现完整音视频处理，但需要在数据模型中预留 `source_spans.time_start_ms` 和 `source_spans.time_end_ms` 表达时间戳，并允许 chunk 类型为 transcript 或 mixed。

### 4.4 Document Block 通用结构

Document Block 是从容器文档中抽取出的中间结构，位于原始文件和 chunk 之间。它保留文档内部顺序和版面位置，用于后续生成 typed chunk。

通用字段：

- id
- file_id
- block_index
- block_type
- raw_content
- page_number，可选
- char_start/char_end，可选
- bbox，可选
- parent_block_id
- context_before
- context_after
- asset_ref
- metadata

block_type 取值：

- heading
- paragraph
- list
- table
- image
- formula
- code
- page_break
- mixed
- unknown

设计约束：

- block_index 必须保持文档阅读顺序。
- table、image、formula 等 block 应保留前后相邻文本，用于后续生成摘要和引用。
- unknown block 不应被丢弃，应进入待检查列表。

### 4.5 Timeline Block 通用结构

Timeline Block 是从音视频中抽取出的中间结构，位于媒体文件和 transcript chunk 之间。它保留时间范围、说话人和关联关键帧。

通用字段：

- id
- file_id
- block_index
- start_time
- end_time
- speaker
- transcript
- keyframe_refs
- screen_ocr_text
- chapter_title
- metadata

设计约束：

- start_time 和 end_time 必须保留，便于问答引用跳转到原视频或音频片段。
- speaker 可以为空，但后续支持说话人分离时应补充。
- keyframe_refs 可以为空，但视频内容后续应能关联关键帧截图。
- transcript 和 screen_ocr_text 都可以成为检索字段。

### 4.6 多类型 Chunk 通用结构

所有 chunk 都应共享一组基础字段，具体类型的结构化信息放入 metadata 中，便于后续扩展。

通用字段：

- id
- file_id
- chunk_type
- raw_content
- edited_content，可选
- summary
- source_spans
- parent_chunk_id，可选
- metadata
- status
- quality_signals
- is_searchable
- created_at
- updated_at

不同类型的 metadata 示例：

```json
{
  "table": {
    "headers": [],
    "rows": [],
    "sheet_name": "Sheet1",
    "row_range": [1, 50]
  },
  "image": {
    "caption": "图 1 系统架构",
    "ocr_text": "",
    "image_path": "",
    "context_before": "",
    "context_after": ""
  },
  "formula": {
    "latex": "",
    "variables": [],
    "context": ""
  }
}
```

设计约束：

- chunk 的核心检索字段可以由 raw_content、edited_content、summary 和 search_text 共同组成。
- metadata 必须保留原始结构信息，避免后续无法重建表格、图片或公式语义。
- source_spans 必须能定位到文件页码、段落、表格区域、图片编号、公式编号或时间范围。
- status 使用统一的 chunk_status，例如 draft、needs_review、verified、ignored、archived。

### 4.7 Source Span 与原文定位

chunk 不应只记录“来自哪个文件”，还应记录它在原始文件中的具体位置。尤其当 chunk 由句号、标点、滑动窗口或父子分块生成时，一个 chunk 可能只覆盖原文某个段落中的一部分文本，必须用 source span 保留精确定位。

通用 source span 字段：

- file_id
- document_block_id
- timeline_block_id，可选
- page_number，可选
- char_start，可选
- char_end，可选
- line_start，可选
- line_end，可选
- bbox，可选
- time_start，可选
- time_end，可选

不同内容类型的定位方式：

- PDF：page_number + document_block_id + char_start/char_end + bbox。
- DOCX：paragraph_index 或 document_block_id + char_start/char_end。
- Markdown：line_start/line_end + column_start/column_end。
- Excel：sheet_name + row_range + column_range。
- 图片/公式：page_number + asset_index + bbox。
- 音视频：time_start + time_end。

PDF 定位要求：

- 普通 PDF 应尽量从文本层提取 word 或 text block 及其 bbox。
- 扫描 PDF 应通过 OCR 获取文字和 bbox。
- chunk 分块时应保留其覆盖的字符范围或 word 范围。
- 前端预览 PDF 时，应能跳转到对应页，并在可行时高亮 bbox 区域。

MVP 可分级实现：

- P0：至少保存 page_number 和 document_block_id，支持跳转到页或文本块。
- P1：保存 char_start/char_end 和 block_bbox，支持较粗粒度高亮。
- P2：保存 word_bboxes，支持句子级或短语级高亮。

用户编辑 chunk 时，不应修改原文件定位。系统应保留 raw_content、edited_content 和 source_spans，确保用户修正文案后仍能回到原始证据位置。

## 5. 阶段一：知识上传

### 5.1 阶段目标

将用户提供的原始知识文件保存为系统事实源，并为后续解析和治理建立元数据。

### 5.2 用户操作

- 上传单个文件。
- 批量上传文件。
- 选择文件所属目录。
- 添加初始标签。
- 填写来源说明，例如部门、项目、会议、网址、负责人。
- 设置文件重要性，例如普通、重要、核心。
- 设置是否自动进入解析流程。
- 查看上传结果和失败原因。

### 5.3 系统能力

- 校验文件类型。
- 校验文件大小。
- 生成文件唯一 ID。
- 保存原始文件。
- 记录上传人、上传时间、文件 hash。
- 检测重复文件。
- 创建初始处理状态。

### 5.4 关键状态

- uploaded：已上传，尚未解析。
- rejected：文件类型、大小或基础校验不符合要求。该状态属于 `knowledge_files.status`，不得进入解析、检索、问答和 Wiki 沉淀。
- queued_for_parse：等待解析。

重复文件不是正式 `knowledge_files.status`。MVP 通过 sha256 或文件名提示疑似重复，仍由用户决定是否继续上传。

### 5.5 MVP 验收

- 用户可以上传 txt、md、pdf、docx 中至少 3 种格式。
- 用户可以为上传文件添加标签和目录。
- 系统可以识别并展示上传状态。
- 重复文件至少能通过文件名或 hash 给出提示。

## 6. 阶段二：内容解析

### 6.1 阶段目标

从原始文件中提取文本、标题、段落、页码和嵌入内容块等结构化信息，为分块和引用溯源提供基础。对于 PDF、Markdown、DOCX 等复合文档，解析结果应先形成 Document Blocks，再进入 typed chunk 生成流程。

### 6.2 用户操作

- 手动触发解析。
- 重新解析文件。
- 选择解析模式，例如快速解析、结构保留解析。
- 查看解析后的全文。
- 查看解析警告，例如空页、乱码、表格丢失。
- 手动修正解析文本。
- 标记某些页面或段落不参与后续处理。MVP 通过 `document_blocks.is_ignored` 持久化该选择。

### 6.3 系统能力

- 按文件容器类型选择解析器。
- 提取纯文本。
- 尽量保留标题和段落结构。
- 识别嵌入的表格、图片、公式和代码块位置，MVP 可先记录为 Document Block 或占位信息。
- 对音视频文件预留 Timeline Block、媒体元数据和待处理状态字段，P2 再进入上传解析主流程。
- 保留 block 阅读顺序。
- 保留嵌入内容与前后文本的上下文关系。
- 记录页码或段落位置。
- 保存解析结果版本。
- 记录解析错误和警告。

### 6.4 关键状态

- parse_pending：待解析。
- parsing：解析中。
- parse_succeeded：解析成功。
- parse_failed：解析失败。
- parse_needs_review：解析成功但需要人工检查。该状态属于 `knowledge_files.status`；对应 `parse_results.status` 仍为 parse_succeeded，并通过 warnings 说明原因。

### 6.5 解析结果字段

- file_id
- parser_name
- parser_version
- raw_text
- document_blocks
- timeline_blocks
- structured_blocks
- asset_placeholders
- warnings
- error_message
- created_at

`document_blocks` 是解析阶段的核心中间产物，记录容器文档内部的标题、段落、表格、图片、公式、代码等 block。

`timeline_blocks` 是媒体解析阶段的核心中间产物，记录音视频中的转写片段、时间戳、说话人、关键帧和屏幕文字。

`asset_placeholders` 用于为后续多类型内容深度解析预留位置。MVP 可以只记录类型、位置和原始描述，不要求完成深度理解。

示例：

```json
[
  {
    "type": "table",
    "position": "page=3, block=5",
    "container": "pdf",
    "status": "detected"
  },
  {
    "type": "image",
    "position": "page=4, figure=2",
    "container": "pdf",
    "status": "detected"
  },
  {
    "type": "transcript",
    "position": "start_time=00:03:20,end_time=00:05:10",
    "container": "mp4",
    "status": "pending_asr"
  }
]
```

### 6.6 MVP 验收

- 用户可以查看解析结果。
- 用户可以查看解析出的 Document Blocks。
- 用户可以重新解析。
- 解析失败时可以看到失败原因。
- 解析后的文本可以定位到来源文件和段落位置。
- 对 PDF、Markdown、DOCX 中嵌入的表格、图片、公式或代码，系统至少能保留 block 类型和来源位置。
- 音视频不作为 MVP 上传解析验收项；数据模型需预留 Timeline Block、transcript chunk 和时间戳 source span，以便 P2 扩展。

## 7. 阶段三：内容分块

### 7.1 阶段目标

将文档块或时间轴片段拆分成适合检索、问答引用和人工治理的 chunk。分块质量直接影响后续检索和问答质量，因此必须允许用户调参和人工修正。

### 7.2 用户操作

- 查看自动分块结果。
- 选择分块策略，例如按标题、按段落、按固定长度、混合策略、父子分块策略。
- 查看 chunk 类型，例如 text、table、image、formula、code、mixed。
- 调整 chunk 最大长度。
- 调整 chunk 重叠长度。
- 调整父块和子块的长度参数。
- 手动合并相邻 chunk，P1 支持。
- 手动拆分过长 chunk，P1 支持。
- 查看父块与子块的关联关系。
- 删除低价值 chunk。
- 标记 chunk 类型，例如正文、表格、目录、附录、噪音。
- 重新生成 chunk。

### 7.3 系统能力

- 根据 Document Blocks 或 Timeline Blocks 生成 typed chunk。
- 为每个 chunk 生成顺序号。
- 记录 chunk 与原始文件位置的映射。
- 记录 chunk 与 Document Block 的映射。
- 记录 transcript chunk 与 Timeline Block 的映射。
- 支持父子分块：父块保留较完整语义上下文，子块用于精确检索。
- 记录 parent_chunk_id 和 child_chunk_ids。
- 计算 chunk 字符数或 token 数。
- 自动识别过短、过长、重复或疑似噪音 chunk。
- 为非文本内容生成占位 chunk，MVP 可先生成 summary 为空的占位对象。
- 支持 chunk 版本更新。

### 7.4 关键状态与操作标记

Chunk 的正式状态使用 `chunk_status`：

- draft：自动生成但未检查。
- needs_review：存在质量信号，建议人工检查。
- verified：人工确认。
- ignored：被用户排除，不参与默认检索、问答和知识单元自动生成。
- archived：因重新分块、重新解析或人工废弃退出默认使用。

以下内容不是正式状态：

- merged/split 是用户操作，应通过新旧 chunk 关系、操作日志或后续 revision 记录。
- parent/child 是结构关系，应通过 `parent_chunk_id` 表达。

### 7.5 分块参数

MVP 支持以下参数：

- strategy：paragraph、heading、fixed_size、hybrid、parent_child。
- max_chars：单个 chunk 最大字符数。
- overlap_chars：相邻 chunk 重叠字符数。
- min_chars：过短 chunk 阈值。
- include_headings：是否将标题带入 chunk。
- parent_max_chars：父块最大字符数。
- child_max_chars：子块最大字符数。
- child_overlap_chars：子块重叠字符数。
- parent_attach_mode：命中子块后带入父块、相邻子块或标题路径。

### 7.6 父子分块策略

父子分块用于同时满足“检索精度”和“上下文完整度”。系统先生成较大的 parent chunk，再在 parent chunk 内生成更小的 child chunk。检索阶段优先索引和召回 child chunk，问答阶段根据 child chunk 找回 parent chunk 或相邻上下文。

推荐结构：

```text
Document Block
  -> Parent Chunk
      -> Child Chunk 1
      -> Child Chunk 2
      -> Child Chunk 3
```

父块职责：

- 保留章节、段落组、完整流程或完整语义单元。
- 承载标题路径、段落背景、表格说明和上下文。
- 作为问答生成时的上下文补充。

子块职责：

- 参与关键词检索和向量检索。
- 保持更短、更聚焦的语义内容。
- 作为引用命中的最小证据单元。

适用场景：

- 长篇制度文档。
- 技术方案。
- 课程资料。
- 法规合同。
- 一段内包含多个知识点的复杂文档。

不适合场景：

- 很短的 FAQ。
- 单行表格数据。
- 已经高度结构化的知识单元。

检索规则：

- 默认检索 child chunk。
- 命中 child chunk 后，可按配置带入 parent chunk。
- 如果 parent chunk 过长，可只带入标题路径和相邻 child chunk。
- 引用展示应优先定位到 child chunk，同时允许用户展开查看 parent chunk。

治理规则：

- 用户可以编辑父块摘要。
- 用户可以忽略低质量子块。
- 用户可以将一个父块下的多个子块合并成知识单元。
- 如果父块被废弃，其子块默认不参与检索。

### 7.7 Chunk 质量信号

系统应为 chunk 提供质量提示，帮助用户发现需要编辑、忽略、合并或重新分块的内容。质量信号默认只作为提示，不应自动删除 chunk。

MVP 支持以下质量信号：

- empty_content：内容为空或接近为空。
- too_short：长度过短，缺少可独立理解的信息。
- too_long：长度过长，可能包含多个主题。
- duplicate：与其他 chunk 高度重复。
- broken_sentence：句子或语义被截断。
- header_footer：疑似页眉、页脚、页码、版权声明。
- low_info_density：信息密度低，例如目录、装饰性文本。
- bad_ocr：存在明显 OCR 乱码或异常字符。
- missing_source_span：缺少原文定位信息。
- mixed_unparsed：包含表格、图片、公式等内容但尚未结构化解析。
- negative_feedback：曾参与问答或检索，但收到用户负反馈。

质量分级建议：

- normal：质量正常，可参与检索和沉淀。
- needs_review：建议人工检查。
- low_quality：低质量，默认降低检索优先级。
- suggest_ignore：建议忽略，需用户确认后才排除。

质量信号写入 `chunks.quality_signals`；正式 `chunks.status` 仍使用 draft、needs_review、verified、ignored、archived。

低质量判定来源：

- 规则检测，例如长度、重复率、乱码比例、来源缺失。
- 用户反馈，例如搜索不相关、答案错误、引用错误。
- 评测结果，例如长期召回但不支持标准答案。

治理规则：

- 用户可以查看质量信号和原因。
- 用户可以编辑 chunk 后重新计算质量信号。
- 用户可以手动覆盖质量状态。
- 已忽略 chunk 默认不参与检索、问答和知识单元生成。

### 7.8 MVP 验收

- 用户可以查看 chunk 列表。
- chunk 列表中可以展示 chunk 类型。
- chunk 列表中可以展示父子关系，MVP 可先展示 parent_chunk_id。
- chunk 列表中可以展示质量信号。
- 用户可以手动编辑 chunk 内容。
- 用户可以将 chunk 标记为忽略。
- 用户可以调整分块参数并重新分块。
- 每个 chunk 可以追溯到文件和位置。
- 每个 chunk 可以追溯到生成它的 Document Block。
- transcript chunk 可以追溯到原媒体文件的时间范围。
- 对检测到但暂未深度解析的表格、图片或公式，系统可以保留占位记录，而不是直接丢弃。

### 7.9 非文本内容分块预留策略

MVP 阶段仅要求保留扩展点，不要求完整多模态理解。

表格预留：

- 小表格后续可整体作为 table chunk。
- 大表格后续可按行区间或 sheet 分块。
- 每个 table chunk 应保留表头、行范围、sheet 名称和来源位置。

图片预留：

- 图片后续可作为 image chunk。
- image chunk 应保留图片路径、图注、OCR 文本、前后文和来源位置。
- 装饰性图片可被标记为 ignored。

公式预留：

- 公式后续可作为 formula chunk。
- formula chunk 应保留 LaTeX、变量解释、上下文和来源位置。
- 公式不应脱离解释段落孤立参与问答。

代码预留：

- 代码后续可作为 code chunk。
- code chunk 应保留语言、代码正文、上下文说明和来源位置。
- 配置、命令和 API 示例应允许作为可检索知识单元沉淀。

## 8. 多类型内容后续扩展方案

### 8.1 扩展目标

后续扩展图、表格、公式、代码、音视频时，不应把它们简单转成一段普通文本，而应形成“原始对象 + 结构化 metadata + 可检索文本 + 可治理知识单元”的组合。

统一扩展链路：

```text
Container File -> Document Block -> Raw Asset -> Specialized Parser -> Typed Chunk -> Searchable Representation -> Knowledge Unit -> Wiki Section -> Evaluation
```

每一种内容类型都需要回答六个问题：

- 如何识别：系统如何知道这是表格、图片、公式、代码或音视频。
- 如何解析：使用什么解析器或模型提取结构信息。
- 如何分块：一个对象作为一块，还是按区域、行、帧、时间段继续拆分。
- 如何检索：检索原文、摘要、结构字段，还是向量表示。
- 如何沉淀：如何变成知识单元或 Wiki 段落。
- 如何评估：如何判断解析和知识沉淀是否可靠。

### 8.2 表格扩展方案

适用对象：

- Excel sheet。
- Word/PDF 中的表格。
- Markdown 表格。
- HTML 表格。
- CSV 文件。

识别方式：

- 文件后缀识别，例如 xlsx、csv。
- PDF、DOCX、HTML 等容器解析器返回的 table block。
- 解析器返回的 table block。
- Markdown 管道符表格。
- PDF 表格检测器识别出的区域。

解析方式：

- Excel：读取 sheet、单元格、合并单元格、表头、行列范围。
- Markdown/HTML：解析表头和行。
- PDF/Word：优先提取表格结构；若失败，退化为表格文本。

分块策略：

- 小表格：整表作为一个 table chunk。
- 大表格：按 sheet、表格区域、行区间切分。
- 宽表格：按主题列或字段组拆分，保留主键列。
- 多表头表格：保留多级表头结构。
- 每个 table chunk 必须携带表头，避免行数据脱离语义。

metadata 建议：

```json
{
  "sheet_name": "评分标准",
  "table_title": "评审维度表",
  "headers": ["维度", "权重", "说明"],
  "rows": [],
  "row_range": [1, 50],
  "column_range": ["A", "C"],
  "primary_columns": ["维度"],
  "source_format": "xlsx"
}
```

检索方式：

- 关键词检索：检索表题、表头、单元格文本、摘要。
- 结构化检索：按列名、指标名、数值范围过滤。
- 语义检索：对表格摘要和行级摘要做 embedding。

沉淀方式：

- 生成“指标解释”类知识单元。
- 生成“对比结论”类知识单元。
- 生成“数据口径”类知识单元。
- 在 Wiki 中展示为表格摘要、关键行摘录和原表链接。

评估指标：

- table_detection_count：检测到的表格数量。
- table_parse_success_rate：表格结构解析成功率。
- header_missing_count：缺失表头数量。
- table_chunk_verified_ratio：已人工确认的 table chunk 比例。

### 8.3 图片扩展方案

适用对象：

- 文档内嵌图片。
- 截图。
- 扫描页。
- 流程图。
- 架构图。
- 图表，例如柱状图、折线图、饼图。

识别方式：

- 文档解析器提取 image block。
- PDF 页面图片区域检测。
- 文件后缀识别，例如 png、jpg、jpeg。
- Markdown 图片引用，例如 `![alt](path)`。
- DOCX 内嵌图片对象。
- OCR 结果提示图片中存在文字。

解析方式：

- OCR：提取图片中的文字。
- 图像描述模型：生成图片语义描述。
- 图表理解：识别坐标轴、图例、趋势和关键数值。
- 流程图理解：提取节点、边和流程顺序。

分块策略：

- 单图作为一个 image chunk。
- 扫描长图按页面或区域拆分。
- 流程图可以拆成总览 chunk 和步骤 chunk。
- 图片 chunk 需要绑定图注、前文和后文。

metadata 建议：

```json
{
  "image_path": "uploads/assets/figure-2.png",
  "caption": "图 2 系统架构",
  "ocr_text": "",
  "visual_description": "该图展示上传、解析、分块、检索、问答的流程。",
  "context_before": "",
  "context_after": "",
  "detected_kind": "architecture_diagram"
}
```

检索方式：

- 检索图注。
- 检索 OCR 文本。
- 检索图像描述。
- 检索关联上下文段落。
- 后续可加入图像 embedding。

沉淀方式：

- 生成“图示说明”知识单元。
- 生成“流程步骤”知识单元。
- 生成“架构组件关系”知识单元。
- Wiki 页面中保留图片预览、摘要和来源链接。

评估指标：

- image_detection_count：检测到的图片数量。
- ocr_text_coverage：OCR 文本覆盖率。
- image_description_verified_ratio：图片描述人工确认比例。
- ignored_decorative_image_count：被标记为装饰图的数量。

### 8.4 公式扩展方案

适用对象：

- PDF/Word 中的数学公式。
- Markdown/LaTeX 公式。
- 图片中的公式。
- 科学、财务、工程计算表达式。

识别方式：

- Markdown `$...$` 或 `$$...$$`。
- Word 公式对象。
- PDF 文本中的公式模式。
- PDF 或 DOCX 中嵌入的 equation block。
- OCR 或公式识别模型检测。

解析方式：

- 保留 LaTeX 或 MathML。
- 提取公式周围解释文本。
- 提取变量、单位和含义。
- 对图片公式进行 OCR 或 LaTeX 识别。

分块策略：

- 公式不应孤立成无上下文 chunk。
- 推荐“公式 + 前后解释段落 + 变量定义”形成 formula chunk。
- 连续推导过程按步骤拆分。
- 结果公式可以绑定到对应概念或规则知识单元。

metadata 建议：

```json
{
  "latex": "F = ma",
  "variables": [
    {"symbol": "F", "meaning": "力", "unit": "N"},
    {"symbol": "m", "meaning": "质量", "unit": "kg"},
    {"symbol": "a", "meaning": "加速度", "unit": "m/s^2"}
  ],
  "context": "该公式用于描述物体受力后的运动状态。",
  "derivation_step": null
}
```

检索方式：

- 检索公式原文。
- 检索变量含义。
- 检索公式上下文说明。
- 后续支持按符号或 LaTeX 片段搜索。

沉淀方式：

- 生成“公式解释”知识单元。
- 生成“变量定义”知识单元。
- 生成“计算规则”知识单元。
- Wiki 页面中保留公式原文、解释、变量表和引用。

评估指标：

- formula_detection_count：检测到的公式数量。
- latex_parse_success_rate：LaTeX 解析成功率。
- variable_extraction_count：提取出的变量数量。
- formula_context_missing_count：缺少上下文解释的公式数量。

### 8.5 代码扩展方案

适用对象：

- Markdown 代码块。
- 文档中的 API 示例。
- 配置文件。
- Shell 命令。
- SQL 脚本。
- 日志片段。

识别方式：

- Markdown fenced code block。
- 文件后缀，例如 py、ts、sql、yaml。
- PDF、DOCX 中等宽字体或代码样式 block。
- 缩进代码块。
- 关键语法模式识别。

解析方式：

- 识别编程语言。
- 保留代码原文。
- 提取函数名、类名、接口名或配置 key。
- 对代码块生成自然语言说明。
- 对 API 示例提取请求方法、路径、参数和响应。

分块策略：

- 小代码块整体作为 code chunk。
- 大代码文件按函数、类、接口或配置段拆分。
- SQL 可按语句拆分。
- 日志可按时间窗口或错误段落拆分。

metadata 建议：

```json
{
  "language": "typescript",
  "symbol_name": "createWikiPage",
  "code": "",
  "explanation": "",
  "api_method": "POST",
  "api_path": "/api/wiki-pages"
}
```

检索方式：

- 检索代码原文。
- 检索语言、函数名、接口路径、配置 key。
- 检索生成的代码说明。
- 后续支持语法级索引。

沉淀方式：

- 生成“接口说明”知识单元。
- 生成“配置说明”知识单元。
- 生成“故障排查”知识单元。
- Wiki 页面中展示代码说明和原始代码引用。

评估指标：

- code_block_count：识别到的代码块数量。
- language_detection_accuracy：语言识别准确率。
- api_example_count：识别到的 API 示例数量。
- code_explanation_verified_ratio：代码说明人工确认比例。

### 8.6 音视频扩展方案

适用对象：

- 会议录音。
- 培训视频。
- 访谈音频。
- 讲座视频。
- 屏幕录制。

识别方式：

- 文件后缀，例如 mp3、wav、mp4、mov。
- 媒体 metadata。
- 上传时用户选择内容类型。

解析方式：

- ASR 转写语音。
- 说话人分离。
- 时间戳对齐。
- 视频关键帧抽取。
- 屏幕文字 OCR。
- 章节或主题切分。
- 将转写片段、关键帧和屏幕文字组织为 Timeline Blocks。

分块策略：

- 按时间窗口分块，例如每 1 到 3 分钟。
- 按语义主题分块。
- 按说话人轮次分块。
- 对培训视频可按章节分块。
- 每个 transcript chunk 必须保留时间戳。
- 视频 mixed chunk 可包含转写文本、关键帧描述和屏幕 OCR 文本。

metadata 建议：

```json
{
  "media_path": "uploads/media/demo.mp4",
  "start_time": "00:03:20",
  "end_time": "00:05:10",
  "speaker": "Speaker 1",
  "transcript": "",
  "keyframes": [],
  "screen_ocr_text": "",
  "chapter_title": "系统架构介绍"
}
```

检索方式：

- 检索转写文本。
- 检索章节标题。
- 检索说话人。
- 检索视频 OCR 文本。
- 后续支持跳转到时间点播放。

沉淀方式：

- 生成“会议纪要”知识单元。
- 生成“行动项”知识单元。
- 生成“培训 FAQ”知识单元。
- 生成“决策记录”知识单元。
- Wiki 页面中保留时间戳引用。
- 对屏幕录制，可沉淀“操作步骤”知识单元。
- 对培训视频，可沉淀“章节摘要”和“知识点清单”。

评估指标：

- asr_success_rate：转写成功率。
- transcript_chunk_count：转写 chunk 数量。
- speaker_diarization_available：是否支持说话人分离。
- timestamp_citation_coverage：时间戳引用覆盖率。
- keyframe_extraction_count：抽取的关键帧数量。
- screen_ocr_coverage：屏幕 OCR 覆盖率。

### 8.7 扩展接入约定

每新增一种内容类型，应至少实现以下接口语义：

```text
detect(file_or_block) -> detected_assets
parse(asset) -> typed_content
chunk(typed_content, params) -> typed_chunks
summarize(typed_chunk) -> searchable_text
curate(typed_chunk) -> knowledge_unit
evaluate(typed_chunk) -> quality_signals
```

工程上建议每种类型以插件式 parser 接入：

```text
parsers/
  text_parser
  table_parser
  image_parser
  formula_parser
  code_parser
  media_parser
```

MVP 可以只实现 text parser，并为其他 parser 提供空实现或占位实现。后续扩展时，只需要新增 parser 和对应 UI 预览，不应修改生命周期主流程。

## 9. 阶段四：知识检索

### 9.1 阶段目标

让用户能检查系统如何召回知识，避免检索过程成为不可解释黑盒。检索不仅服务问答，也服务知识整理和 Wiki 生成。

### 9.2 用户操作

- 输入关键词或自然语言查询。
- 选择检索范围，例如全部文件、指定目录、指定标签、指定文件。
- 选择检索对象，例如文件、chunk、知识单元、Wiki 页面。
- 选择内容类型过滤，例如只看文本、表格、图片说明、公式或代码。
- 选择是否只检索已确认知识。
- 查看召回结果和匹配原因。
- 查看命中的子块以及其父块上下文。
- 手动调整某条结果是否应参与问答上下文。
- 将检索结果保存为主题集合。
- 基于检索结果生成 Topic Wiki，P1 支持。

### 9.3 系统能力

- 支持关键词检索。
- 支持按标签、目录、状态过滤。
- 展示匹配字段，例如标题、正文、标签、引用。
- 展示召回分数，MVP 可使用简单相关度分数。
- 支持命中子块后扩展父块上下文。
- 支持将结果作为问答上下文。
- 支持将结果作为 Wiki 生成素材。

### 9.4 检索结果类型

- file：原始文件。
- chunk：文本片段。
- knowledge_unit：知识单元。
- wiki_page：Wiki 页面。

检索结果还应展示内容类型，例如 text、table、image、formula、code。MVP 可以只展示 text 和 detected placeholder，后续再扩展专用预览。

### 9.5 MVP 验收

- 用户可以按关键词搜索 chunk、知识单元和 Wiki 页面。
- 用户可以按标签和状态过滤搜索结果。
- 搜索结果展示匹配片段。
- 用户可以查看某条结果的来源。

## 10. 阶段五：知识沉淀

### 10.1 阶段目标

将一次性解析结果、检索结果、问答过程、用户反馈和评测样本沉淀为可维护的知识资产，包括 Knowledge Unit、Wiki Page 和 Evaluation Dataset。

Wiki Page 还应支持沉淀为 Wiki Revision。它表示一次可审查、可对比、可回滚的 Wiki Markdown 快照，用于记录 AI 生成、人工编辑、重新生成和确认发布的历史。数据库中的 Wiki Page 负责当前可见内容、治理状态、引用关系、检索字段和 source span；Wiki Revision 负责保存历史版本、变更说明和引用快照。

### 10.2 用户操作

- 从 chunk 生成候选知识单元。
- 从搜索结果生成主题知识单元。
- 从问答结果保存知识单元。
- 查看一次问答命中的 retrieved_contexts 和引用来源。
- 将用户问题、AI 回答、retrieved_contexts、引用来源和用户反馈保存为对话样本。
- 将高质量对话样本加入评测集。
- 将负反馈对话加入待优化队列。
- 手动创建知识单元。
- 编辑知识单元标题、正文、类型、标签、适用范围。
- 将表格、图片、公式或代码 chunk 沉淀为知识单元，MVP 可先通过手动摘要完成。
- 合并重复知识单元，P1 支持。
- 拆分过大的知识单元，P1 支持。
- 维护知识单元引用来源。
- 将知识单元标记为已确认或已废弃。
- 将多个知识单元组织成 Wiki 页面。
- 查看 Wiki 页面修订历史，P1 支持。
- 将 Wiki 页面回滚到指定历史版本，P1 支持。

### 10.3 系统能力

- 基于 chunk 生成摘要式知识单元。
- 基于多个 chunk 生成主题式知识单元。
- 保存问答会话、单轮问题、回答、retrieved_contexts 和引用来源。
- 保存用户反馈，例如有帮助、无帮助、答案错误、引用错误、缺少来源。
- 从问答记录生成评测样本。
- 识别相似知识单元，提示可能重复。
- 记录知识单元来源。
- 支持知识单元版本历史，MVP 可先记录更新时间和编辑人。
- 支持 Wiki 页面关联多个知识单元。
- 支持 Wiki Revision 快照，MVP 预留字段，P1 启用版本对比和回滚。

### 10.4 对话与召回沉淀

用户的真实问题、系统召回的 chunk、AI 的回答、引用来源和用户反馈，是知识库优化的重要资产。KnowWeave 应将它们作为一类可治理数据，而不是只作为运行日志保存。

一次问答记录应包含：

- question：用户问题。
- answer：AI 回答。
- retrieved_contexts：本次召回的上下文列表，可能包含 chunk、Knowledge Unit、Wiki Page 或 file。
- cited_sources：答案实际引用的来源。
- retrieval_params：检索范围、top_k、过滤条件、检索策略。
- feedback：用户反馈。
- feedback_reason：反馈原因。
- created_at：创建时间。

可沉淀方向：

- 将高质量回答保存为 FAQ Knowledge Unit。
- 将高频问题聚合为 Topic Wiki，P1 支持。
- 将引用错误样本加入评测集。
- 将召回失败问题加入检索优化队列。
- 将用户补充答案转化为人工知识单元。

### 10.5 评测数据集构建

评测集用于支撑准确率、召回率、引用质量等指标的计算。评测样本既可以由人工创建，也可以从真实用户对话和反馈中沉淀。

评测样本字段：

- question
- expected_answer
- expected_source_chunks
- expected_source_files
- tags
- difficulty
- created_from，例如 manual、chat_feedback、wiki_review
- status，例如 draft、verified、archived

构建方式：

- 人工创建标准问题。
- 从用户正反馈问答中提取高质量样本。
- 从用户负反馈问答中提取待修复样本。
- 从 Wiki 页面自动生成候选问题，再由人工确认。
- 从知识单元生成 FAQ 问题。

闭环流程：

```text
User Question -> Retrieved Chunks -> Answer -> Feedback -> Evaluation Sample -> Metric -> Optimization Task -> Knowledge Curation
```

MVP 可以先保存问答记录和用户反馈，评测样本构建可以先采用人工确认方式。

### 10.6 知识单元类型

MVP 支持以下类型：

- concept：概念解释。
- rule：规则制度。
- process：流程步骤。
- faq：问答知识。
- decision：结论或决策。
- glossary：术语。

### 10.7 沉淀状态

- draft：草稿。
- pending_review：待审核。
- verified：已确认。
- archived：已废弃。

### 10.8 MVP 验收

- 用户可以从 chunk 创建知识单元。
- 用户可以从问答记录创建知识单元。
- 用户可以查看问答命中的 retrieved_contexts。
- 用户可以保存用户问题、回答、retrieved_contexts 和反馈。
- 用户可以将对话样本加入评测集，MVP 可先标记为候选样本。
- 用户可以编辑知识单元。
- 用户可以维护知识单元标签和状态。
- 用户可以查看知识单元引用来源。
- 用户可以从知识单元生成或更新 Wiki 页面。

## 11. 阶段六：知识评估

### 11.1 阶段目标

让用户可以判断知识库处理效果是否可靠，并定位问题发生在哪个阶段：解析错、分块差、检索不到、Wiki 失真，还是问答引用不准确。

### 11.2 用户操作

- 查看文件级处理质量。
- 查看 chunk 质量提示。
- 查看不同内容类型的处理覆盖情况。
- 对检索结果标记相关或不相关。
- 对 AI 回答标记有帮助、无帮助、有幻觉、引用错误。
- 对 Wiki 页面标记准确、需修改、过期。
- 创建评测问题集。
- 从问答记录和用户反馈中生成评测样本。
- 运行评测问题集，查看命中率和引用覆盖率。

### 11.3 系统能力

- 统计解析成功率。
- 统计 chunk 数量、平均长度、忽略比例。
- 统计搜索无结果次数。
- 统计问答引用覆盖率。
- 记录用户反馈。
- 记录问答召回上下文。
- 支持从反馈生成评测样本。
- 基于反馈生成待优化清单。

### 11.4 评估指标

MVP 支持以下指标：

- parse_success_rate：解析成功率。
- avg_chunk_length：平均 chunk 长度。
- ignored_chunk_ratio：被忽略 chunk 占比。
- search_hit_count：搜索命中数量。
- retrieval_precision：检索准确率，返回结果中被标记为相关的比例。
- retrieval_recall：检索召回率，标准答案来源中被检索命中的比例。
- answer_accuracy：问答准确率，回答内容被人工或评测集判定正确的比例。
- citation_precision：引用准确率，回答引用中真正支撑答案的比例。
- citation_recall：引用召回率，标准支撑来源中被答案引用覆盖的比例。
- verified_knowledge_ratio：已确认知识单元比例。
- evaluation_sample_count：评测样本数量。
- feedback_to_dataset_conversion_rate：反馈转评测样本比例。
- answer_citation_coverage：回答引用覆盖率。
- negative_feedback_count：负反馈数量。

准确率和召回率需要依赖评测集或人工反馈：

- 检索准确率适合用用户对搜索结果的相关性反馈计算。
- 检索召回率需要预先维护问题与标准来源的映射。
- 问答准确率需要人工标注或基准问题集。
- 引用准确率关注“引用是否真的支撑答案”。
- 引用召回率关注“关键来源是否被漏掉”。

MVP 可以先通过人工反馈近似计算准确率，召回率作为评测集能力的预留指标。

后续为多类型内容预留以下指标：

- table_detection_count：检测到的表格数量。
- image_detection_count：检测到的图片数量。
- formula_detection_count：检测到的公式数量。
- asset_placeholder_ratio：已检测但尚未深度解析的内容占比。
- multimodal_chunk_verified_ratio：已确认的非文本 chunk 占比。

### 11.5 MVP 验收

- 用户可以对搜索结果给出相关性反馈。
- 用户可以对问答结果给出质量反馈。
- 系统可以保存问答记录、retrieved_contexts 和用户反馈。
- 用户可以将问答记录标记为评测样本候选。
- 用户可以看到文件的基础处理统计。
- 用户可以看到待审核知识单元数量。

## 12. 生命周期控制台

### 12.1 页面目标

生命周期控制台用于展示知识库整体运行状态，帮助用户发现需要处理的文件、chunk、知识单元、Wiki 页面和评估问题。

### 12.2 MVP 信息区

- 文件总数。
- 解析成功文件数。
- 解析失败文件数。
- chunk 总数。
- 待审核知识单元数量。
- 已确认知识单元数量。
- Wiki 页面数量。
- 问答记录数量。
- 评测样本数量。
- 最近负反馈数量。

### 12.3 待办列表

- 待解析文件。
- 解析失败文件。
- 需要人工检查的 chunk。
- 待审核知识单元。
- 缺少引用的 Wiki 页面。
- 收到负反馈的问答记录。
- 待确认的评测样本。
- 召回失败或引用错误的问题。

## 13. 操作权限与责任边界

MVP 可以采用单用户模式，但产品语义上需要区分操作责任：

- AI 可以生成候选结果。
- 知识管理员可以整理和维护。
- 领域专家负责确认可信知识。
- 普通用户可以搜索、问答和反馈。

已确认知识应记录确认人和确认时间，便于后续追责和更新。

## 14. MVP 优先级

### 14.1 P0 必须完成

- 上传阶段：上传、标签、目录、状态。
- 解析阶段：解析结果查看、重新解析、失败原因。
- 分块阶段：chunk 列表、编辑、忽略、重新分块。
- 检索阶段：关键词搜索、过滤、来源查看。
- 沉淀阶段：创建和编辑知识单元、状态维护。
- 评估阶段：问答反馈、搜索反馈、基础统计、问答记录沉淀。

### 14.2 P1 尽量完成

- 批量上传。
- 分块参数可视化调节。
- 向量检索。
- 知识单元合并与拆分。
- 从问答结果沉淀知识单元。
- 评测问题集。
- 从用户反馈自动生成评测样本候选。

### 14.3 P2 后续扩展

- 自动重复知识检测。
- 自动质量评分。
- 表格结构化解析。
- 图片 OCR 和图像描述。
- 公式识别与 LaTeX 保留。
- 代码块语言识别。
- 多人协作审核流。
- 知识版本 diff。

## 15. 验收场景

### 15.1 场景一：用户修正解析结果

1. 用户上传一个文档。
2. 系统自动解析文本。
3. 用户发现解析文本中存在无关页眉。
4. 用户编辑解析结果或标记相关段落不参与处理。
5. 用户重新分块。

验收结果：后续 chunk 不再包含被排除内容。

### 15.2 场景二：用户调整分块策略

1. 用户查看 chunk 列表。
2. 用户发现 chunk 过长。
3. 用户将 max_chars 调小。
4. 用户重新分块。
5. 系统生成新的 chunk 版本。

验收结果：chunk 数量增加，单个 chunk 长度下降，来源映射保留。

### 15.3 场景三：用户确认可信知识

1. 系统从 chunk 生成候选知识单元。
2. 用户编辑知识单元标题和正文。
3. 用户补充标签和引用来源。
4. 用户将状态改为 verified。

验收结果：该知识单元在问答召回中优先使用。

### 15.4 场景四：用户评估问答质量

1. 用户向知识库提问。
2. 系统返回答案和引用。
3. 用户发现引用不准确。
4. 用户标记为引用错误。
5. 系统将该问题加入待优化列表。

验收结果：控制台能看到负反馈记录。

## 16. 与后续技术 Spec 的关系

本文定义产品行为和用户操作边界。后续技术文档需要继续细化：

- 数据模型：文件、解析结果、chunk、知识单元、Wiki、反馈、评测集。
- API：上传、解析、分块、检索、沉淀、评估各阶段接口。
- 前端：生命周期控制台和各阶段操作页面。
- 任务系统：解析、分块、索引、Wiki 生成的同步或异步执行方式。
