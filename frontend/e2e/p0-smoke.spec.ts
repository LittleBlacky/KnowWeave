import { expect, test, type Page, type Route } from "@playwright/test";
import path from "node:path";

const apiPattern = "http://localhost:8000/api/v1/**";

const policyFile = {
  id: "file_policy",
  name: "company_policy.md",
  original_filename: "company_policy.md",
  file_type: "md",
  mime_type: "text/markdown",
  size_bytes: 256,
  sha256: "abc123",
  directory_path: "",
  status: "uploaded",
};

const sourceSpan = {
  id: "span_policy",
  document_block_id: "block_policy",
  page_number: null,
  char_start: 0,
  char_end: 64,
  line_start: 1,
  line_end: 3,
  preview_text: "System access requests require manager approval.",
};

const policyChunk = {
  id: "chunk_policy",
  file_id: "file_policy",
  parse_result_id: "parse_policy",
  document_block_id: "block_policy",
  chunk_index: 0,
  chunk_type: "text",
  raw_content: "System access requests require manager approval before provisioning.",
  edited_content: null,
  is_manually_edited: false,
  status: "draft" as const,
  summary: null,
  quality_signals: [],
  char_count: 65,
  search_text: "System access requests require manager approval before provisioning.",
  is_searchable: true,
  source_spans: [sourceSpan],
};

type P0Chunk = Omit<typeof policyChunk, "edited_content" | "status"> & {
  edited_content: string | null;
  status: "draft" | "ignored" | "verified";
};

const searchResult = {
  result_id: "chunk_policy",
  result_type: "chunk",
  title: "company_policy.md",
  preview_text: "System access requests require manager approval before provisioning.",
  score: "1.0000",
  rank: 1,
  source: {
    file_id: "file_policy",
    file_name: "company_policy.md",
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

const feedback = {
  id: "feedback_chat_message",
  target_type: "chat_message",
  target_id: "msg_chat_001",
  feedback_type: "answer_wrong",
  comment: "Need the approval timing.",
  status: "open",
  metadata_: { source: "playwright" },
  created_at: "2026-05-26T00:00:00Z",
  updated_at: "2026-05-26T00:00:00Z",
};

const evaluationSample = {
  id: "eval_chat_message",
  question: "Who approves system access requests?",
  expected_answer: "Managers approve system access requests.",
  expected_source_files: ["file_policy"],
  expected_source_chunks: ["chunk_policy"],
  created_from: "feedback",
  source_chat_message_id: "msg_chat_001",
  source_feedback_id: "feedback_chat_message",
  status: "candidate",
  difficulty: "easy",
  metadata_: { source: "playwright" },
  created_at: "2026-05-26T00:00:00Z",
  updated_at: "2026-05-26T00:00:00Z",
};

test("P0 browser smoke covers evidence upload, search, chat, feedback and evaluation", async ({
  page,
}) => {
  await setupP0ApiRoutes(page);

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Evidence Governance Overview" })).toBeVisible();

  await page.getByRole("link", { name: "Files" }).click();
  await expect(page.getByRole("heading", { name: "Upload Evidence" })).toBeVisible();

  const demoFile = path.join(__dirname, "..", "..", "data", "demo", "company_policy.md");
  await page.locator("#evidence-file").setInputFiles(demoFile);
  await expect(page.getByRole("status")).toContainText("Uploaded company_policy.md");
  await expect(page.getByRole("cell", { exact: true, name: "company_policy.md" })).toBeVisible();

  await page.getByRole("button", { name: "Parse company_policy.md" }).click();
  await expect(page.getByText("parse_succeeded")).toBeVisible();
  await page.getByRole("button", { name: "Build chunks for company_policy.md" }).click();
  await expect(page.getByText("1 chunks built")).toBeVisible();

  await page.getByRole("link", { name: "Chunks" }).click();
  await expect(page.getByRole("heading", { name: "Chunk Workspace" })).toBeVisible();
  await expect(page.getByRole("textbox", { name: "Edited chunk content" })).toHaveValue(
    "System access requests require manager approval before provisioning.",
  );
  await page.getByRole("button", { name: "Verify chunk" }).click();
  await expect(page.getByText("verified")).toBeVisible();

  await page.getByRole("link", { name: "Search" }).click();
  await page.getByLabel("Search query").fill("manager approval");
  await page.getByRole("button", { name: "Run search" }).click();
  await expect(page.getByText("run_search_001")).toBeVisible();
  await page.getByRole("button", { name: /company_policy\.md/i }).click();
  await expect(page.getByText("Lines 1-3")).toBeVisible();

  await page.getByRole("link", { name: "Chat" }).click();
  await page.getByLabel("Chat question").fill("Who approves system access requests?");
  await page.getByRole("button", { name: "Send question" }).click();
  await expect(page.getByText("Fake answer: manager approval required.")).toBeVisible();
  await page.getByRole("button", { name: "S1 System access requests require manager approval." }).click();
  await expect(page.getByRole("heading", { name: "Citation source" })).toBeVisible();

  await page.getByLabel("Feedback type").selectOption("answer_wrong");
  await page.getByLabel("Feedback comment").fill("Need the approval timing.");
  await page.getByRole("button", { name: "Submit feedback" }).click();
  await expect(page.getByText("feedback_chat_message")).toBeVisible();
  await page.getByRole("button", { name: "Create evaluation candidate" }).click();
  await expect(page.getByText("eval_chat_message")).toBeVisible();

  await page.getByRole("link", { name: "Evaluation" }).click();
  await expect(page.getByRole("heading", { name: "Evaluation Candidates" })).toBeVisible();
  await expect(page.getByText("Who approves system access requests?")).toBeVisible();
  await expect(page.getByText("chunk_policy")).toBeVisible();
});

async function setupP0ApiRoutes(page: Page) {
  let currentChunk: P0Chunk = policyChunk;
  let evaluationCreated = false;

  await page.route(apiPattern, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const pathname = url.pathname.replace("/api/v1", "");
    const method = request.method();

    if (method === "GET" && pathname === "/files") {
      return fulfillJson(route, listEnvelope([policyFile]));
    }

    if (method === "POST" && pathname === "/files/upload") {
      return fulfillJson(route, envelope(policyFile), 201);
    }

    if (method === "POST" && pathname === "/files/file_policy/parse") {
      return fulfillJson(route, envelope({
        id: "parse_policy",
        file_id: "file_policy",
        parser_name: "markdown_parser",
        parser_version: "0.1.0",
        status: "parse_succeeded",
        warnings: [],
        block_count: 2,
      }));
    }

    if (method === "POST" && pathname === "/files/file_policy/chunks/build") {
      return fulfillJson(route, listEnvelope([currentChunk]));
    }

    if (method === "GET" && pathname === "/files/file_policy/chunks") {
      return fulfillJson(route, listEnvelope([currentChunk]));
    }

    if (method === "PATCH" && pathname === "/chunks/chunk_policy") {
      const body = request.postDataJSON() as { edited_content?: string };
      currentChunk = {
        ...currentChunk,
        edited_content: body.edited_content ?? null,
        is_manually_edited: Boolean(body.edited_content),
        search_text: body.edited_content ?? currentChunk.raw_content,
      };
      return fulfillJson(route, envelope(currentChunk));
    }

    if (method === "POST" && pathname === "/chunks/chunk_policy/verify") {
      currentChunk = { ...currentChunk, status: "verified", is_searchable: true };
      return fulfillJson(route, envelope(currentChunk));
    }

    if (method === "POST" && pathname === "/chunks/chunk_policy/ignore") {
      currentChunk = { ...currentChunk, status: "ignored", is_searchable: false };
      return fulfillJson(route, envelope(currentChunk));
    }

    if (method === "POST" && pathname === "/search") {
      return fulfillJson(route, envelope({
        retrieval_run_id: "run_search_001",
        query: "manager approval",
        strategy: "keyword",
        results: [searchResult],
      }));
    }

    if (method === "POST" && pathname === "/chat/sessions") {
      return fulfillJson(route, envelope({
        id: "session_chat_001",
        title: "New chat",
        scope: {},
        created_at: "2026-05-26T00:00:00Z",
        updated_at: "2026-05-26T00:00:00Z",
      }), 201);
    }

    if (method === "POST" && pathname === "/chat/sessions/session_chat_001/messages") {
      return route.fulfill({
        body: [
          'event: start\ndata: {"message_id":"msg_chat_001","retrieval_run_id":"run_chat_001"}',
          `event: retrieval\ndata: ${JSON.stringify({
            retrieval_run_id: "run_chat_001",
            results: [searchResult],
          })}`,
          'event: delta\ndata: {"message_id":"msg_chat_001","delta":"Fake answer: "}',
          'event: delta\ndata: {"message_id":"msg_chat_001","delta":"manager approval required."}',
          `event: citations\ndata: ${JSON.stringify({
            message_id: "msg_chat_001",
            citations: [
              {
                key: "S1",
                label: "S1",
                chunk_id: "chunk_policy",
                source_span_id: "span_policy",
                preview_text: "System access requests require manager approval.",
                source_available: true,
              },
            ],
          })}`,
          'event: done\ndata: {"message_id":"msg_chat_001","status":"completed"}',
        ].join("\n\n"),
        contentType: "text/event-stream",
      });
    }

    if (method === "POST" && pathname === "/feedback") {
      return fulfillJson(route, envelope(feedback), 201);
    }

    if (method === "POST" && pathname === "/feedback/feedback_chat_message/to-evaluation-sample") {
      evaluationCreated = true;
      return fulfillJson(route, envelope(evaluationSample), 201);
    }

    if (method === "GET" && pathname === "/evaluation-samples") {
      return fulfillJson(route, listEnvelope(evaluationCreated ? [evaluationSample] : []));
    }

    return route.fulfill({
      contentType: "application/json",
      status: 404,
      body: JSON.stringify({
        data: null,
        error: { code: "E2E_ROUTE_NOT_FOUND", message: `${method} ${pathname}` },
        request_id: "req_e2e_not_found",
      }),
    });
  });
}

function envelope(data: unknown) {
  return {
    data,
    error: null,
    request_id: "req_e2e",
  };
}

function listEnvelope(items: unknown[]) {
  return envelope({
    items,
    total: items.length,
  });
}

function fulfillJson(route: Route, payload: unknown, status = 200) {
  return route.fulfill({
    body: JSON.stringify(payload),
    contentType: "application/json",
    status,
  });
}
