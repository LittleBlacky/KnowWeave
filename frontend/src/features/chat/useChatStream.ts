import { apiClient } from "@/shared/api/client";
import type { SearchResult } from "@/shared/api/knowweave";
import { useState } from "react";

export type ChatSession = {
  id: string;
  title: string;
  scope: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type ChatCitation = {
  key: string;
  label: string | null;
  file_id: string | null;
  chunk_id: string | null;
  source_span_id: string | null;
  preview_text: string;
  source_available: boolean;
};

export type ChatStreamEvent =
  | { type: "start"; message_id: string; retrieval_run_id: string }
  | { type: "retrieval"; retrieval_run_id: string; results: SearchResult[] }
  | { type: "delta"; message_id: string; delta: string }
  | { type: "citations"; message_id: string; citations: ChatCitation[] }
  | { type: "done"; message_id: string; status: string }
  | { type: "error"; message_id?: string; status?: string; message: string };

export type ChatStreamStatus = "idle" | "submitting" | "streaming" | "completed" | "error";

export type ChatStreamState = {
  answer: string;
  citations: ChatCitation[];
  error: string | null;
  messageId: string | null;
  retrievalRunId: string | null;
  results: SearchResult[];
  status: ChatStreamStatus;
};

const initialState: ChatStreamState = {
  answer: "",
  citations: [],
  error: null,
  messageId: null,
  retrievalRunId: null,
  results: [],
  status: "idle",
};

export function useChatStream() {
  const [state, setState] = useState<ChatStreamState>(initialState);

  async function sendMessage(question: string) {
    if (!question.trim()) {
      return;
    }

    setState({ ...initialState, status: "submitting" });

    try {
      const session = await createChatSession("New chat");
      setState((current) => ({ ...current, status: "streaming" }));
      await streamChatMessage(session.id, question, (event) =>
        setState((current) => reduceChatStreamEvent(current, event)),
      );
    } catch (error) {
      setState((current) => ({
        ...current,
        error: error instanceof Error ? error.message : "Chat request failed.",
        status: "error",
      }));
    }
  }

  return { sendMessage, state };
}

export function reduceChatStreamEvent(
  state: ChatStreamState,
  event: ChatStreamEvent,
): ChatStreamState {
  if (event.type === "start") {
    return {
      ...state,
      messageId: event.message_id,
      retrievalRunId: event.retrieval_run_id,
      status: "streaming",
    };
  }

  if (event.type === "retrieval") {
    return {
      ...state,
      retrievalRunId: event.retrieval_run_id,
      results: event.results,
      status: "streaming",
    };
  }

  if (event.type === "delta") {
    return {
      ...state,
      answer: `${state.answer}${event.delta}`,
      messageId: event.message_id,
      status: "streaming",
    };
  }

  if (event.type === "citations") {
    return {
      ...state,
      citations: event.citations,
      messageId: event.message_id,
      status: "streaming",
    };
  }

  if (event.type === "done") {
    return {
      ...state,
      messageId: event.message_id,
      status: event.status === "completed" ? "completed" : "streaming",
    };
  }

  return {
    ...state,
    error: event.message,
    messageId: event.message_id ?? state.messageId,
    status: "error",
  };
}

export function createChatSession(title = "New chat") {
  return apiClient.post<ChatSession>("/chat/sessions", { title });
}

export async function streamChatMessage(
  sessionId: string,
  question: string,
  onEvent: (event: ChatStreamEvent) => void,
  topK = 5,
) {
  const response = await fetch(apiClient.url(`/chat/sessions/${sessionId}/messages`), {
    body: JSON.stringify({ question, top_k: topK }),
    headers: { "content-type": "application/json" },
    method: "POST",
  });

  if (!response.ok || !response.body) {
    throw new Error(response.statusText || "Chat request failed.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";
    for (const eventText of events) {
      const event = parseSseEvent(eventText);
      if (event) {
        onEvent(event);
      }
    }
  }

  if (buffer.trim()) {
    const event = parseSseEvent(buffer);
    if (event) {
      onEvent(event);
    }
  }
}

export function parseSseEvent(eventText: string): ChatStreamEvent | null {
  let eventType = "";
  let data = "";
  for (const line of eventText.split(/\r?\n/)) {
    if (line.startsWith("event: ")) {
      eventType = line.slice("event: ".length);
    }
    if (line.startsWith("data: ")) {
      data = line.slice("data: ".length);
    }
  }
  if (!eventType || !data) {
    return null;
  }
  return { ...JSON.parse(data), type: eventType } as ChatStreamEvent;
}
