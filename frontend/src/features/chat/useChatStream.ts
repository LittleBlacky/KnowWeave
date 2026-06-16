import {
  createChatSession,
  deleteChatSession,
  getChatSession,
  listChatSessions,
  type ChatSession,
  type SearchResult,
} from "@/shared/api/knowweave";
import {apiClient} from "@/shared/api/client";
import {useCallback, useEffect, useState} from "react";

export type {ChatSession};

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
  | {type: "start"; message_id: string; retrieval_run_id: string}
  | {type: "retrieval"; retrieval_run_id: string; results: SearchResult[]}
  | {type: "delta"; message_id: string; delta: string}
  | {type: "citations"; message_id: string; citations: ChatCitation[]}
  | {type: "done"; message_id: string; status: string}
  | {type: "error"; message_id?: string; status?: string; message: string};

export type MessageStatus = "pending" | "streaming" | "completed" | "error";

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: ChatCitation[];
  retrievalResults: SearchResult[];
  retrievalRunId: string | null;
  messageId: string | null;
  status: MessageStatus;
  error: string | null;
  createdAt: number;
};

export type ChatStreamStatus = "idle" | "submitting" | "streaming";

export type ChatState = {
  sessions: ChatSession[];
  activeSessionId: string | null;
  messages: Message[];
  status: ChatStreamStatus;
};

let _msgSeq = 0;
function nextMsgId() {
  _msgSeq += 1;
  return `msg-${Date.now()}-${_msgSeq}`;
}

function makeMessage(overrides: Partial<Message> = {}): Message {
  return {
    id: nextMsgId(),
    role: "assistant",
    content: "",
    citations: [],
    retrievalResults: [],
    retrievalRunId: null,
    messageId: null,
    status: "pending",
    error: null,
    createdAt: Date.now(),
    ...overrides,
  };
}

const initialState: ChatState = {
  sessions: [],
  activeSessionId: null,
  messages: [],
  status: "idle",
};

export function useChatStream() {
  const [state, setState] = useState<ChatState>(initialState);

  // Load sessions on mount
  useEffect(() => {
    void loadSessions();
  }, []);

  async function loadSessions() {
    try {
      const res = await listChatSessions();
      setState((prev) => ({...prev, sessions: res.items}));
    } catch {
      // silently ignore
    }
  }

  const updateLastAssistant = useCallback(
    (patch: Partial<Message> & {_delta?: string}) => {
      setState((prev) => {
        const msgs = [...prev.messages];
        const lastIdx = msgs.length - 1;
        if (lastIdx < 0 || msgs[lastIdx].role !== "assistant") return prev;

        const current = msgs[lastIdx];
        if (patch._delta) {
          msgs[lastIdx] = {
            ...current,
            content: current.content + patch._delta,
            messageId: patch.messageId ?? current.messageId,
            status: "streaming",
          };
        } else {
          msgs[lastIdx] = {...current, ...(patch as Message)};
        }
        return {...prev, messages: msgs};
      });
    },
    [],
  );

  async function sendMessage(question: string) {
    const q = question.trim();
    if (!q) return;

    const userMsg = makeMessage({
      role: "user",
      content: q,
      status: "completed",
    });
    const assistantMsg = makeMessage({role: "assistant", status: "pending"});

    setState((prev) => ({
      ...prev,
      messages: [...prev.messages, userMsg, assistantMsg],
      status: "submitting",
    }));

    try {
      let sessionId = state.activeSessionId;

      // Create a new session if none active
      if (!sessionId) {
        const session = await createChatSession(q.slice(0, 30));
        sessionId = session.id;
        setState((prev) => ({
          ...prev,
          activeSessionId: sessionId,
          sessions: [session, ...prev.sessions],
          status: "streaming",
        }));
      } else {
        setState((prev) => ({...prev, status: "streaming"}));
      }

      const onEvent = (event: ChatStreamEvent) => {
        updateLastAssistant(reduceMessagePatch(event));
      };

      await streamChatMessage(sessionId!, q, onEvent);

      // Refresh session list (title may have changed)
      void loadSessions();

      setState((prev) => ({...prev, status: "idle"}));
    } catch (error) {
      updateLastAssistant({
        error: error instanceof Error ? error.message : "Chat request failed.",
        status: "error",
      });
      setState((prev) => ({...prev, status: "idle"}));
    }
  }

  async function newChat() {
    setState((prev) => ({
      ...prev,
      activeSessionId: null,
      messages: [],
      status: "idle",
    }));
  }

  async function switchSession(sessionId: string) {
    setState((prev) => ({...prev, status: "idle"}));

    try {
      const detail = await getChatSession(sessionId);

      // Map backend messages to frontend Message type
      const messages: Message[] = [];
      for (const m of detail.messages) {
        // Add user message (the question isn't stored separately, so we
        // show the assistant answer only). We'll pair them heuristically.
        if (m.role === "user") {
          messages.push(
            makeMessage({
              id: `user-${m.id}`,
              role: "user",
              content: m.content_markdown,
              status: "completed",
              createdAt: new Date(m.created_at).getTime(),
            }),
          );
        } else {
          messages.push(
            makeMessage({
              id: `assistant-${m.id}`,
              role: "assistant",
              content: m.content_markdown,
              messageId: m.id,
              status: m.status === "completed" ? "completed" : "streaming",
              createdAt: new Date(m.created_at).getTime(),
            }),
          );
        }
      }

      setState((prev) => ({
        ...prev,
        activeSessionId: sessionId,
        messages,
      }));
    } catch {
      // Session may have been deleted
      setState((prev) => ({
        ...prev,
        activeSessionId: null,
        messages: [],
      }));
    }
  }

  async function deleteActiveSession() {
    const sid = state.activeSessionId;
    if (!sid) return;

    try {
      await deleteChatSession(sid);
    } catch {
      // ignore — backend may not support DELETE
    }

    setState((prev) => ({
      ...prev,
      activeSessionId: null,
      messages: [],
      sessions: prev.sessions.filter((s) => s.id !== sid),
    }));
  }

  return {
    state,
    sendMessage,
    newChat,
    switchSession,
    deleteActiveSession,
    loadSessions,
  };
}

/** Reduce a single SSE event into a partial Message update. */
export function reduceMessagePatch(event: ChatStreamEvent): Partial<Message> {
  if (event.type === "start") {
    return {
      messageId: event.message_id,
      retrievalRunId: event.retrieval_run_id,
      status: "streaming",
    };
  }

  if (event.type === "retrieval") {
    return {
      retrievalRunId: event.retrieval_run_id,
      retrievalResults: event.results,
      status: "streaming",
    };
  }

  if (event.type === "delta") {
    return {
      messageId: event.message_id,
      status: "streaming",
      _delta: event.delta,
    } as Partial<Message> & {_delta: string};
  }

  if (event.type === "citations") {
    return {
      citations: event.citations,
      messageId: event.message_id,
      status: "streaming",
    };
  }

  if (event.type === "done") {
    return {
      messageId: event.message_id,
      status: event.status === "completed" ? "completed" : "streaming",
    };
  }

  return {
    error: event.message,
    messageId: event.message_id ?? undefined,
    status: "error",
  };
}

export async function streamChatMessage(
  sessionId: string,
  question: string,
  onEvent: (event: ChatStreamEvent) => void,
  topK = 5,
) {
  const response = await fetch(
    apiClient.url(`/chat/sessions/${sessionId}/messages`),
    {
      body: JSON.stringify({question, top_k: topK}),
      headers: {"content-type": "application/json"},
      method: "POST",
    },
  );

  if (!response.ok || !response.body) {
    throw new Error(response.statusText || "Chat request failed.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const {done, value} = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, {stream: true});
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
  return {...JSON.parse(data), type: eventType} as ChatStreamEvent;
}

