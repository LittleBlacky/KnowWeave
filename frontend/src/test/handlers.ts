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
