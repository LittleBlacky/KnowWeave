import { http, HttpResponse } from "msw";

const policyFile = {
  id: "file_policy",
  name: "policy.md",
  original_filename: "policy.md",
  file_type: "md",
  mime_type: "text/markdown",
  size_bytes: 37,
  sha256: "abc123",
  directory_path: "",
  status: "uploaded",
};

const sourceSpan = {
  id: "span_policy",
  document_block_id: "block_policy",
  page_number: null,
  char_start: 0,
  char_end: 37,
  line_start: 1,
  line_end: 3,
  preview_text: "Leave requests need approval.",
};

const policyChunk = {
  id: "chunk_policy",
  file_id: "file_policy",
  parse_result_id: "parse_policy",
  document_block_id: "block_policy",
  chunk_index: 0,
  chunk_type: "text",
  raw_content: "Leave requests need approval.",
  edited_content: null,
  is_manually_edited: false,
  status: "draft",
  summary: null,
  quality_signals: [],
  char_count: 29,
  search_text: "Leave requests need approval.",
  is_searchable: true,
  source_spans: [sourceSpan],
};

const searchResult = {
  result_id: "chunk_policy",
  result_type: "chunk",
  title: "policy.md",
  preview_text: "Leave requests need approval.",
  score: "1.0000",
  rank: 1,
  source: {
    file_id: "file_policy",
    file_name: "policy.md",
    source_span_id: "span_policy",
    page_number: null,
    line_start: 1,
    line_end: 3,
    source_available: true,
  },
  status: {
    chunk_status: "draft",
    source_file_deleted: false,
  },
  metadata: {
    chunk_index: 0,
    retrieval_strategy: "keyword",
    matched_fields: ["search_text"],
  },
};

const tag = {
  id: "tag_hr",
  name: "HR",
  description: "People policy",
  color: "#2563eb",
  binding_count: 1,
  created_at: "2026-05-26T00:00:00Z",
  updated_at: "2026-05-26T00:00:00Z",
};

const knowledgeUnit = {
  id: "ku_leave_approval",
  title: "Leave approval rule",
  unit_type: "rule",
  content: "Leave requests require manager approval.",
  summary: "Manager approval is required.",
  status: "pending_review",
  trust_level: null,
  applicable_scope: "HR policies",
  created_from: "chunk",
  search_text: "Leave approval rule\nManager approval is required.\nLeave requests require manager approval.",
  metadata_: {},
  source_count: 1,
  tags: [tag],
  created_at: "2026-05-26T00:00:00Z",
  updated_at: "2026-05-26T00:00:00Z",
  verified_at: null,
  archived_at: null,
};

const knowledgeUnitSource = {
  id: "ku_source_leave_approval",
  knowledge_unit_id: "ku_leave_approval",
  file_id: "file_policy",
  chunk_id: "chunk_policy",
  source_span_id: "span_policy",
  source_type: "chunk",
  source_label: "S1",
  source_available: true,
  created_at: "2026-05-26T00:00:00Z",
};

const wikiPage = {
  id: "wiki_policy",
  title: "policy.md",
  wiki_type: "document_wiki",
  status: "draft",
  summary: "Draft wiki generated from 1 chunks.",
  content_markdown: "# policy.md\n\n## Source Summary\n- Leave requests require manager approval. [S1]",
  source_file_id: "file_policy",
  generation_prompt_version: "fake_wiki_v1",
  search_text: "Leave requests require manager approval.",
  metadata_: { source_chunk_count: 1 },
  created_at: "2026-05-26T00:00:00Z",
  updated_at: "2026-05-26T00:00:00Z",
  verified_at: null,
};

const wikiCitation = {
  id: "citation_wiki_policy",
  target_type: "wiki_page",
  target_id: "wiki_policy",
  file_id: "file_policy",
  chunk_id: "chunk_policy",
  source_span_id: "span_policy",
  label: "S1",
  preview_text: "Leave requests require manager approval.",
  source_available: true,
};

const feedback = {
  id: "feedback_wiki_policy",
  target_type: "wiki_page",
  target_id: "wiki_policy",
  feedback_type: "wiki_needs_update",
  comment: "Clarify manager approval timing.",
  status: "open",
  metadata_: { source: "component-test" },
  created_at: "2026-05-26T00:00:00Z",
  updated_at: "2026-05-26T00:00:00Z",
};

const evaluationSample = {
  id: "eval_leave_approval",
  question: "Who approves leave requests?",
  expected_answer: "Managers approve leave requests.",
  expected_source_files: ["file_policy"],
  expected_source_chunks: ["chunk_policy"],
  created_from: "feedback",
  source_chat_message_id: null,
  source_feedback_id: "feedback_wiki_policy",
  status: "candidate",
  difficulty: "easy",
  metadata_: { feedback_type: "wiki_needs_update" },
  created_at: "2026-05-26T00:00:00Z",
  updated_at: "2026-05-26T00:00:00Z",
};

export const handlers = [
  http.get("http://localhost/api/v1/health", () =>
    HttpResponse.json({
      status: "ok",
      service: "knowweave-frontend-msw",
      version: "0.1.0",
    }),
  ),
  http.get("http://localhost:8000/api/v1/files", () =>
    HttpResponse.json({
      data: {
        items: [policyFile],
        total: 1,
      },
      error: null,
      request_id: "req_files",
    }),
  ),
  http.post("http://localhost:8000/api/v1/files/upload", async ({ request }) => {
    const rawBody = await request.clone().text();
    const filename = rawBody.match(/filename="([^"]+)"/)?.[1];
    const form = await request.formData();
    const file = form.get("file");
    const fallbackName =
      typeof file === "object" && file !== null && "name" in file
        ? String(file.name)
        : "uploaded.md";
    const name = filename && filename !== "blob" ? filename : fallbackName === "blob" ? "policy.md" : fallbackName;

    return HttpResponse.json({
      data: {
        ...policyFile,
        id: "file_uploaded",
        name,
        original_filename: name,
      },
      error: null,
      request_id: "req_upload",
    });
  }),
  http.post("http://localhost:8000/api/v1/files/:fileId/parse", ({ params }) =>
    HttpResponse.json({
      data: {
        id: "parse_policy",
        file_id: params.fileId,
        parser_name: "markdown_parser",
        parser_version: "0.1.0",
        status: "parse_succeeded",
        warnings: [],
        block_count: 2,
      },
      error: null,
      request_id: "req_parse",
    }),
  ),
  http.post("http://localhost:8000/api/v1/files/:fileId/chunks/build", () =>
    HttpResponse.json({
      data: {
        items: [policyChunk],
        total: 1,
      },
      error: null,
      request_id: "req_build_chunks",
    }),
  ),
  http.get("http://localhost:8000/api/v1/files/:fileId/chunks", () =>
    HttpResponse.json({
      data: {
        items: [policyChunk],
        total: 1,
      },
      error: null,
      request_id: "req_file_chunks",
    }),
  ),
  http.patch("http://localhost:8000/api/v1/chunks/:chunkId", async ({ request }) => {
    const body = (await request.json()) as { edited_content?: string };

    return HttpResponse.json({
      data: {
        ...policyChunk,
        edited_content: body.edited_content ?? null,
        is_manually_edited: Boolean(body.edited_content),
        search_text: body.edited_content ?? policyChunk.raw_content,
      },
      error: null,
      request_id: "req_chunk_update",
    });
  }),
  http.post("http://localhost:8000/api/v1/chunks/:chunkId/ignore", () =>
    HttpResponse.json({
      data: {
        ...policyChunk,
        status: "ignored",
        is_searchable: false,
      },
      error: null,
      request_id: "req_chunk_ignore",
    }),
  ),
  http.post("http://localhost:8000/api/v1/chunks/:chunkId/verify", () =>
    HttpResponse.json({
      data: {
        ...policyChunk,
        status: "verified",
        is_searchable: true,
      },
      error: null,
      request_id: "req_chunk_verify",
    }),
  ),
  http.post("http://localhost:8000/api/v1/search", () =>
    HttpResponse.json({
      data: {
        retrieval_run_id: "run_search_001",
        query: "approval",
        strategy: "keyword",
        results: [searchResult],
      },
      error: null,
      request_id: "req_search",
    }),
  ),
  http.get("http://localhost:8000/api/v1/tags", () =>
    HttpResponse.json({
      data: {
        items: [tag],
        total: 1,
      },
      error: null,
      request_id: "req_tag_list",
    }),
  ),
  http.post("http://localhost:8000/api/v1/tags", async ({ request }) => {
    const body = (await request.json()) as { name?: string; description?: string; color?: string };

    return HttpResponse.json(
      {
        data: {
          ...tag,
          id: "tag_new",
          name: body.name ?? "New tag",
          description: body.description ?? null,
          color: body.color ?? null,
          binding_count: 0,
        },
        error: null,
        request_id: "req_tag_create",
      },
      { status: 201 },
    );
  }),
  http.post("http://localhost:8000/api/v1/tag-bindings", async ({ request }) => {
    const body = (await request.json()) as {
      tag_id: string;
      target_type: string;
      target_id: string;
    };

    return HttpResponse.json(
      {
        data: {
          id: "tag_binding_001",
          tag_id: body.tag_id,
          target_type: body.target_type,
          target_id: body.target_id,
          created_at: "2026-05-26T00:00:00Z",
        },
        error: null,
        request_id: "req_tag_binding_create",
      },
      { status: 201 },
    );
  }),
  http.get("http://localhost:8000/api/v1/knowledge-units", () =>
    HttpResponse.json({
      data: {
        items: [knowledgeUnit],
        total: 1,
      },
      error: null,
      request_id: "req_knowledge_unit_list",
    }),
  ),
  http.get("http://localhost:8000/api/v1/knowledge-units/:knowledgeUnitId", () =>
    HttpResponse.json({
      data: {
        ...knowledgeUnit,
        sources: [knowledgeUnitSource],
      },
      error: null,
      request_id: "req_knowledge_unit_detail",
    }),
  ),
  http.patch("http://localhost:8000/api/v1/knowledge-units/:knowledgeUnitId", async ({ request }) => {
    const body = (await request.json()) as { status?: string; title?: string; content?: string };

    return HttpResponse.json({
      data: {
        ...knowledgeUnit,
        title: body.title ?? knowledgeUnit.title,
        content: body.content ?? knowledgeUnit.content,
        status: body.status ?? knowledgeUnit.status,
        verified_at: body.status === "verified" ? "2026-05-26T00:00:00Z" : null,
      },
      error: null,
      request_id: "req_knowledge_unit_update",
    });
  }),
  http.get("http://localhost:8000/api/v1/wiki", () =>
    HttpResponse.json({
      data: {
        items: [wikiPage],
        total: 1,
      },
      error: null,
      request_id: "req_wiki_list",
    }),
  ),
  http.get("http://localhost:8000/api/v1/wiki/:wikiId", () =>
    HttpResponse.json({
      data: wikiPage,
      error: null,
      request_id: "req_wiki_detail",
    }),
  ),
  http.patch("http://localhost:8000/api/v1/wiki/:wikiId", async ({ request }) => {
    const body = (await request.json()) as {
      change_summary?: string;
      content_markdown?: string;
      status?: string;
    };

    return HttpResponse.json({
      data: {
        ...wikiPage,
        content_markdown: body.content_markdown ?? wikiPage.content_markdown,
        status: body.status ?? wikiPage.status,
        metadata_: {
          ...wikiPage.metadata_,
          last_change_summary: body.change_summary,
        },
      },
      error: null,
      request_id: "req_wiki_update",
    });
  }),
  http.get("http://localhost:8000/api/v1/wiki/:wikiId/citations", () =>
    HttpResponse.json({
      data: {
        items: [wikiCitation],
        total: 1,
      },
      error: null,
      request_id: "req_wiki_citations",
    }),
  ),
  http.post("http://localhost:8000/api/v1/feedback", async ({ request }) => {
    const body = (await request.json()) as {
      target_type: string;
      target_id: string;
      feedback_type: string;
      comment?: string;
      metadata?: Record<string, unknown>;
    };

    return HttpResponse.json(
      {
        data: {
          ...feedback,
          target_type: body.target_type,
          target_id: body.target_id,
          feedback_type: body.feedback_type,
          comment: body.comment ?? null,
          metadata_: body.metadata ?? {},
        },
        error: null,
        request_id: "req_feedback_create",
      },
      { status: 201 },
    );
  }),
  http.post("http://localhost:8000/api/v1/feedback/:feedbackId/to-evaluation-sample", () =>
    HttpResponse.json(
      {
        data: evaluationSample,
        error: null,
        request_id: "req_feedback_to_evaluation",
      },
      { status: 201 },
    ),
  ),
  http.get("http://localhost:8000/api/v1/evaluation-samples", () =>
    HttpResponse.json({
      data: {
        items: [evaluationSample],
        total: 1,
      },
      error: null,
      request_id: "req_evaluation_sample_list",
    }),
  ),
  http.post("http://localhost:8000/api/v1/chat/sessions", () =>
    HttpResponse.json(
      {
        data: {
          id: "session_chat_001",
          title: "New chat",
          scope: {},
          created_at: "2026-05-26T00:00:00Z",
          updated_at: "2026-05-26T00:00:00Z",
        },
        error: null,
        request_id: "req_chat_session_create",
      },
      { status: 201 },
    ),
  ),
  http.post("http://localhost:8000/api/v1/chat/sessions/:sessionId/messages", () =>
    HttpResponse.text(
      [
        'event: start\ndata: {"message_id":"msg_chat_001","retrieval_run_id":"run_chat_001"}',
        `event: retrieval\ndata: ${JSON.stringify({
          retrieval_run_id: "run_chat_001",
          results: [searchResult],
        })}`,
        'event: delta\ndata: {"message_id":"msg_chat_001","delta":"Fake answer: "}',
        'event: delta\ndata: {"message_id":"msg_chat_001","delta":"approval"}',
        `event: citations\ndata: ${JSON.stringify({
          message_id: "msg_chat_001",
          citations: [
            {
              key: "S1",
              label: "S1",
              file_id: "file_policy",
              chunk_id: "chunk_policy",
              source_span_id: "span_policy",
              preview_text: "Leave requests need approval.",
              source_available: true,
            },
          ],
        })}`,
        'event: done\ndata: {"message_id":"msg_chat_001","status":"completed"}',
      ].join("\n\n"),
      {
        headers: {
          "content-type": "text/event-stream",
        },
      },
    ),
  ),
];
