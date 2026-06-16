import {describe, expect, it} from "vitest";

import {parseSseEvent, reduceMessagePatch, type Message} from "./useChatStream";

const baseMessage: Message = {
  id: "test-1",
  role: "assistant",
  content: "",
  citations: [],
  retrievalResults: [],
  retrievalRunId: null,
  messageId: null,
  status: "pending",
  error: null,
  createdAt: Date.now(),
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

  it("reduces start, delta, citations and done events into message patches", () => {
    const startPatch = reduceMessagePatch({
      type: "start",
      message_id: "msg_001",
      retrieval_run_id: "run_001",
    });
    expect(startPatch).toMatchObject({
      messageId: "msg_001",
      retrievalRunId: "run_001",
      status: "streaming",
    });

    const deltaPatch = reduceMessagePatch({
      type: "delta",
      message_id: "msg_001",
      delta: "Leave requests",
    });
    expect(deltaPatch).toMatchObject({
      messageId: "msg_001",
      status: "streaming",
      _delta: "Leave requests",
    });

    const citationsPatch = reduceMessagePatch({
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
    expect(citationsPatch).toMatchObject({
      messageId: "msg_001",
      citations: [{key: "S1"}],
      status: "streaming",
    });

    const donePatch = reduceMessagePatch({
      type: "done",
      message_id: "msg_001",
      status: "completed",
    });
    expect(donePatch).toMatchObject({
      messageId: "msg_001",
      status: "completed",
    });
  });

  it("stores readable backend stream errors", () => {
    const patch = reduceMessagePatch({
      type: "error",
      message: "Provider unavailable.",
      message_id: "msg_001",
      status: "failed",
    });

    expect(patch).toMatchObject({
      error: "Provider unavailable.",
      messageId: "msg_001",
      status: "error",
    });
  });
});

