const fs = require("fs");
const path = require("path");

const docs = [
  {
    file: "00-project-dashboard.md",
    token: "UPgrdeRzmoDbW9xLEy5ceoREnxg",
    title: "00 KnowWeave 项目可视化驾驶舱",
    type: "项目驾驶舱",
    version: "v0.7",
    status: "草案",
    owner: "KnowWeave 项目组",
    summary:
      "作为 KnowWeave 的可视化入口，汇总项目定位、生命周期、路线图、任务拆分、风险和评估指标。",
    focus: ["项目总览", "P0/P1/P2 路线图", "任务拆分"],
  },
  {
    file: "README.md",
    token: "S38ud9nWaoARSdxUgqVc4CnInOc",
    title: "README KnowWeave 文档索引",
    type: "文档索引",
    version: "v1.0",
    status: "草案",
    owner: "KnowWeave 项目组",
    summary:
      "本页作为 KnowWeave 规格文档入口，帮助读者按产品、生命周期、架构、数据模型、工程实现和演示验收的顺序理解项目。",
    focus: ["阅读顺序", "文档边界", "工程骨架计划"],
  },
  {
    file: "01-product-spec.md",
    token: "PBGhdgdMsobarCxqC0DcYOxwnff",
    title: "01 KnowWeave 产品需求规格说明书",
    type: "产品规格",
    version: "v1.2",
    status: "草案",
    owner: "产品与项目评审",
    summary:
      "定义 KnowWeave 的产品定位、用户角色、核心概念、MVP 范围与验收标准，是后续技术规格的上游约束。",
    focus: ["产品定位", "MVP 范围", "验收标准"],
  },
  {
    file: "02-knowledge-lifecycle-spec.md",
    token: "VTz2d59wnoKC2BxSQQAccNclnHb",
    title: "02 KnowWeave 知识生命周期细粒度管理规格说明书",
    type: "业务生命周期规格",
    version: "v1.0",
    status: "草案",
    owner: "知识治理与产品",
    summary:
      "描述知识从上传、解析、分块、检索、沉淀到评估的完整闭环，强调可见、可干预、可追溯。",
    focus: ["知识生命周期", "人工治理", "评估闭环"],
  },
  {
    file: "03-system-architecture-spec.md",
    token: "NIiudpd3kogQRjxX017cI9BLnAc",
    title: "03 KnowWeave 系统架构规格说明书",
    type: "系统架构规格",
    version: "v0.9",
    status: "草案",
    owner: "架构与工程",
    summary:
      "定义 KnowWeave 的模块边界、技术选型、数据流、存储边界和后续扩展策略，服务小而完整的 MVP。",
    focus: ["模块边界", "数据流", "技术选型"],
  },
  {
    file: "04-data-model-spec.md",
    token: "AZ1AdcNAFogRy2xPYapcIuRGngb",
    title: "04 KnowWeave 数据模型规格说明书",
    type: "数据模型规格",
    version: "v0.8",
    status: "草案",
    owner: "后端与数据",
    summary:
      "定义核心实体、状态枚举、关系、软删除、source span 定位和 Wiki Revision，为工程实现提供数据契约。",
    focus: ["核心实体", "状态与关系", "Source Span"],
  },
  {
    file: "05-ingestion-spec.md",
    token: "H5Jed6J7FoPp3CxjtXfccL4Sn0f",
    title: "05 KnowWeave Ingestion 规格说明书",
    type: "Ingestion 规格",
    version: "v0.3",
    status: "草案",
    owner: "后端与解析链路",
    summary:
      "定义文件上传、解析、Document Block、Chunking、Source Span 写入、重处理与验收场景。",
    focus: ["上传解析", "Chunking", "重处理"],
  },
  {
    file: "06-llm-wiki-spec.md",
    token: "Peq8dY8yFoFbhuxR6n6cMdE9nbc",
    title: "06 KnowWeave LLM Wiki 规格说明书",
    type: "LLM Wiki 规格",
    version: "v0.1",
    status: "草案",
    owner: "知识治理与产品",
    summary:
      "定义 Document Wiki、Topic Wiki、FAQ Wiki 的生成、引用、状态、修订历史和反馈闭环。",
    focus: ["Wiki 生成", "Citation", "Revision"],
  },
  {
    file: "07-search-and-chat-spec.md",
    token: "WlurdH1rqojtL5xfGpAcH4hSnsf",
    title: "07 KnowWeave 搜索与问答规格说明书",
    type: "搜索与问答规格",
    version: "v0.4",
    status: "草案",
    owner: "搜索、Chat 与评测闭环",
    summary:
      "定义搜索、RAG 问答、上下文组织、SSE 流式输出、引用和反馈评估闭环。",
    focus: ["Search Result", "Chat SSE", "Feedback"],
  },
  {
    file: "08-frontend-spec.md",
    token: "EJOvdwWTNotceGxHK8hcXfZunug",
    title: "08 KnowWeave 前端交互规格说明书",
    type: "前端交互规格",
    version: "v0.3",
    status: "草案",
    owner: "前端与产品体验",
    summary:
      "定义页面信息架构、chunk 治理 UI、Source Viewer、Chat/Wiki/Search 交互和流式 Markdown 渲染。",
    focus: ["页面结构", "Source Viewer", "交互状态"],
  },
  {
    file: "09-acceptance-test-spec.md",
    token: "D6Y3dUb1doiMCixLmA6cwGwgn5f",
    title: "09 KnowWeave 验收测试规格说明书",
    type: "验收测试规格",
    version: "v0.2",
    status: "草案",
    owner: "质量与演示验收",
    summary:
      "定义 P0/P1/P2 验收测试、演示剧本、检查清单、失败分级和验收报告模板。",
    focus: ["P0 验收", "演示剧本", "失败分级"],
  },
  {
    file: "10-evaluation-spec.md",
    token: "MCyMdRcTOo0pJUx7lAUcPmkln4g",
    title: "10 KnowWeave 评测与反馈闭环规格说明书",
    type: "评测闭环规格",
    version: "v0.2",
    status: "草案",
    owner: "评测与反馈闭环",
    summary:
      "定义评测样本、评测集、评测运行、指标计算、失败分析和回归评估。",
    focus: ["Evaluation Sample", "Metrics", "Regression"],
  },
  {
    file: "11-backend-implementation-spec.md",
    token: "Y8v2d9YfVozlWQxJDHZcXf9tnPe",
    title: "11 KnowWeave 后端实现规格说明书",
    type: "后端实现规格",
    version: "v0.1",
    status: "草案",
    owner: "后端工程",
    summary:
      "定义 FastAPI 后端实现、Service 边界、Provider 抽象、迁移、SSE 和测试策略。",
    focus: ["FastAPI", "Service Layer", "API Contract"],
  },
  {
    file: "12-frontend-implementation-spec.md",
    token: "IJaQdYCZyozksAxfx7Rc8NZXnNc",
    title: "12 KnowWeave 前端实现规格说明书",
    type: "前端实现规格",
    version: "v0.1",
    status: "草案",
    owner: "前端工程",
    summary:
      "定义 Next.js 前端实现、路由、组件边界、API client、SSE、状态管理和测试策略。",
    focus: ["Next.js", "API Client", "SSE Hook"],
  },
  {
    file: "13-devops-and-demo-spec.md",
    token: "N2PkdaBx3ob2IlxbS7WcTMN2nze",
    title: "13 KnowWeave DevOps 与 Demo 规格说明书",
    type: "DevOps 与 Demo 规格",
    version: "v0.1",
    status: "草案",
    owner: "工程交付与演示验收",
    summary:
      "定义 Docker Compose、环境变量、演示数据、Smoke 脚本和答辩演示流程。",
    focus: ["Docker Compose", "Demo Data", "P0 Smoke"],
  },
  {
    file: "14-tdd-task-breakdown.md",
    token: "TpVVdcbv7orBV8xmW4ec15fznEG",
    title: "14 KnowWeave TDD 任务拆解说明书",
    type: "TDD 任务拆解",
    version: "v0.1",
    status: "草案",
    owner: "工程交付与质量",
    summary:
      "定义 P0 工程实现的 TDD 任务拆分、测试先行要求、执行顺序和完成标准。",
    focus: ["TDD 执行规则", "任务拆分", "测试验收"],
  },
];

const root = path.resolve(__dirname, "..");
const inputDirCandidates = [
  path.join(root, "KnowWeave", "docs"),
  path.join(root, "docs"),
];
const inputDir = inputDirCandidates.find((candidate) => fs.existsSync(candidate));
if (!inputDir) {
  throw new Error(`Cannot find KnowWeave docs directory from ${root}`);
}
const tokenMapPath = path.join(inputDir, "feishu", "knowweave-doc-tokens.json");
const outputDir = path.join(root, ".tmp", "knowweave-feishu-xml");
fs.mkdirSync(outputDir, { recursive: true });

function loadTokenMap() {
  if (!fs.existsSync(tokenMapPath)) return new Map();
  const raw = JSON.parse(fs.readFileSync(tokenMapPath, "utf8"));
  return new Map((raw.documents || []).map((item) => [item.file, item]));
}

const tokenMap = loadTokenMap();
for (const doc of docs) {
  const remote = tokenMap.get(doc.file);
  if (remote?.token) doc.token = remote.token;
  if (remote?.url) doc.url = remote.url;
}

function escapeXml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function inline(text) {
  let escaped = escapeXml(text);
  escaped = escaped.replace(/`([^`]+)`/g, "<code>$1</code>");
  escaped = escaped.replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>");
  escaped = escaped.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  return escaped;
}

function isTableLine(line) {
  return /^\s*\|.*\|\s*$/.test(line);
}

function isTableDivider(line) {
  return /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);
}

function splitTable(line) {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

function tableToXml(lines) {
  const rows = lines.filter((line) => !isTableDivider(line)).map(splitTable);
  if (!rows.length) return "";
  const header = rows[0];
  const body = rows.slice(1);
  const width = Math.max(...rows.map((row) => row.length));
  const headXml = header
    .concat(Array(Math.max(0, width - header.length)).fill(""))
    .map((cell) => `<th background-color="light-gray">${inline(cell)}</th>`)
    .join("");
  const bodyXml = body
    .map((row) => {
      const normalized = row.concat(Array(Math.max(0, width - row.length)).fill(""));
      return `<tr>${normalized
        .map((cell) => `<td vertical-align="top">${inline(cell)}</td>`)
        .join("")}</tr>`;
    })
    .join("");
  return `<table><thead><tr>${headXml}</tr></thead><tbody>${bodyXml}</tbody></table>`;
}

function listToXml(items, ordered) {
  const tag = ordered ? "ol" : "ul";
  const rows = items
    .map((item) => {
      const body = ordered ? item.replace(/^\s*\d+\.\s+/, "") : item.replace(/^\s*[-*]\s+/, "");
      const seq = ordered ? ' seq="auto"' : "";
      return `<li${seq}>${inline(body)}</li>`;
    })
    .join("");
  return `<${tag}>${rows}</${tag}>`;
}

function convertMarkdown(markdown, doc) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const out = [];
  let i = 0;

  function flushParagraph(buffer) {
    if (!buffer.length) return;
    out.push(`<p>${inline(buffer.join(" "))}</p>`);
    buffer.length = 0;
  }

  const paragraph = [];
  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed) {
      flushParagraph(paragraph);
      i += 1;
      continue;
    }

    if (/^!\[.*\]\(.+\)$/.test(trimmed)) {
      flushParagraph(paragraph);
      const alt = trimmed.match(/^!\[(.*)\]\((.+)\)$/);
      out.push(`<callout emoji="📌" background-color="light-gray" border-color="gray"><p>原文图片占位：${inline(alt?.[1] || "图片")}（${inline(alt?.[2] || "")}）</p></callout>`);
      i += 1;
      continue;
    }

    if (/^```/.test(trimmed)) {
      flushParagraph(paragraph);
      const lang = trimmed.replace(/^```/, "").trim() || "text";
      const code = [];
      i += 1;
      while (i < lines.length && !/^```/.test(lines[i].trim())) {
        code.push(lines[i]);
        i += 1;
      }
      if (i < lines.length) i += 1;
      out.push(`<pre lang="${escapeXml(lang)}"><code>${escapeXml(code.join("\n"))}</code></pre>`);
      continue;
    }

    if (/^#{1,6}\s+/.test(trimmed)) {
      flushParagraph(paragraph);
      const match = trimmed.match(/^(#{1,6})\s+(.*)$/);
      const level = Math.min(match[1].length, 4);
      const text = match[2].trim();
      const docTitleWithoutPrefix = doc.title.replace(/^(README|\d{2})\s+/, "");
      if (level === 1 && (text === doc.title || text === docTitleWithoutPrefix)) {
        i += 1;
        continue;
      }
      if (level <= 2) out.push("<hr/>");
      out.push(`<h${level}>${inline(text)}</h${level}>`);
      i += 1;
      continue;
    }

    if (isTableLine(trimmed)) {
      flushParagraph(paragraph);
      const tableLines = [];
      while (i < lines.length && isTableLine(lines[i].trim())) {
        tableLines.push(lines[i]);
        i += 1;
      }
      out.push(tableToXml(tableLines));
      continue;
    }

    if (/^\s*[-*]\s+/.test(line)) {
      flushParagraph(paragraph);
      const items = [];
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        items.push(lines[i]);
        i += 1;
      }
      out.push(listToXml(items, false));
      continue;
    }

    if (/^\s*\d+\.\s+/.test(line)) {
      flushParagraph(paragraph);
      const items = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        items.push(lines[i]);
        i += 1;
      }
      out.push(listToXml(items, true));
      continue;
    }

    if (/^>\s?/.test(trimmed)) {
      flushParagraph(paragraph);
      const quote = [];
      while (i < lines.length && /^>\s?/.test(lines[i].trim())) {
        quote.push(lines[i].trim().replace(/^>\s?/, ""));
        i += 1;
      }
      out.push(`<blockquote>${inline(quote.join(" "))}</blockquote>`);
      continue;
    }

    paragraph.push(trimmed);
    i += 1;
  }
  flushParagraph(paragraph);
  return out.join("\n");
}

function frontMatter(doc) {
  const focusList = doc.focus.map((item) => `<li>${escapeXml(item)}</li>`).join("");
  return [
    `<title>${escapeXml(doc.title)}</title>`,
    `<callout emoji="ℹ️" background-color="light-blue" border-color="blue" text-color="blue">`,
    `<p><b>快速摘要：</b>${escapeXml(doc.summary)}</p>`,
    `</callout>`,
    `<table>`,
    `<thead><tr><th background-color="light-gray">字段</th><th background-color="light-gray">内容</th></tr></thead>`,
    `<tbody>`,
    `<tr><td>文档类型</td><td>${escapeXml(doc.type)}</td></tr>`,
    `<tr><td>当前版本</td><td>${escapeXml(doc.version)}</td></tr>`,
    `<tr><td>状态</td><td>${escapeXml(doc.status)}</td></tr>`,
    `<tr><td>责任范围</td><td>${escapeXml(doc.owner)}</td></tr>`,
    `</tbody>`,
    `</table>`,
    `<grid>`,
    `<column width-ratio="0.5"><callout emoji="📌" background-color="light-green" border-color="green"><p><b>阅读重点</b></p><ul>${focusList}</ul></callout></column>`,
    `<column width-ratio="0.5"><callout emoji="✅" background-color="light-yellow" border-color="yellow"><p><b>使用方式</b></p><ul><li>先看快速摘要，再进入对应章节。</li><li>涉及实现细节时，以表格、清单和代码块为准。</li><li>评审时优先检查 MVP 范围和验收项。</li></ul></callout></column>`,
    `</grid>`,
    `<hr/>`,
  ].join("\n");
}

const manifest = [];
for (const doc of docs) {
  const input = path.join(inputDir, doc.file);
  const markdown = fs.readFileSync(input, "utf8");
  const xml = `${frontMatter(doc)}\n${convertMarkdown(markdown, doc)}\n`;
  const output = path.join(outputDir, doc.file.replace(/\.md$/, ".xml"));
  fs.writeFileSync(output, xml, "utf8");
  manifest.push({ ...doc, output });
}

fs.writeFileSync(path.join(outputDir, "manifest.json"), JSON.stringify(manifest, null, 2), "utf8");
console.log(`Generated ${manifest.length} Feishu XML files in ${outputDir}`);
