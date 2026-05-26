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
];
