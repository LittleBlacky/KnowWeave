import { describe, expect, it } from "vitest";

import { parseSseEvent, reduceChatStreamEvent, type ChatStreamState } from "./useChatStream";

const emptyState: ChatStreamState = {
  answer: "",
  citations: [],
  error: null,
  messageId: null,
  retrievalRunId: null,
  results: [],
  status: "idle",
};

describe("parseSseEvent", () => {
  it("normalizes backend SSE events into typed chat events", () => {
    const event = parseSseEvent(
      'event: delta\ndata: {"message_id":"msg_001","delta":"Leave requests"}',
    );

    expect(event).toEqual({
      type: "delta",
      message_id: "msg_001",
      delta: "Leave requests",
    });
  });

  it("updates stream state for start, delta, citations and done events", () => {
    const started = reduceChatStreamEvent(emptyState, {
      type: "start",
      message_id: "msg_001",
      retrieval_run_id: "run_001",
    });
    const withDelta = reduceChatStreamEvent(started, {
      type: "delta",
      message_id: "msg_001",
      delta: "Leave requests",
    });
    const withCitations = reduceChatStreamEvent(withDelta, {
      type: "citations",
      message_id: "msg_001",
      citations: [
        {
          chunk_id: "chunk_policy",
          file_id: "file_policy",
          key: "S1",
          label: "S1",
          preview_text: "Leave requests need approval.",
          source_available: true,
          source_span_id: "span_policy",
        },
      ],
    });
    const done = reduceChatStreamEvent(withCitations, {
      type: "done",
      message_id: "msg_001",
      status: "completed",
    });

    expect(done).toMatchObject({
      answer: "Leave requests",
      citations: [{ key: "S1" }],
      messageId: "msg_001",
      retrievalRunId: "run_001",
      status: "completed",
    });
  });

  it("stores readable backend stream errors", () => {
    const state = reduceChatStreamEvent(emptyState, {
      type: "error",
      message: "Provider unavailable.",
      message_id: "msg_001",
      status: "failed",
    });

    expect(state).toMatchObject({
      error: "Provider unavailable.",
      messageId: "msg_001",
      status: "error",
    });
  });
});
