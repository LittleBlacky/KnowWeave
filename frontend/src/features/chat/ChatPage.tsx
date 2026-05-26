"use client";

import { MessageSquareText, Send } from "lucide-react";
import { useState } from "react";

import { FeedbackDialog } from "@/features/feedback/FeedbackDialog";
import { SourceLocatorPanel } from "@/features/source-viewer/SourceLocatorPanel";
import type { SearchResult } from "@/shared/api/knowweave";

import { useChatStream, type ChatCitation, type ChatStreamStatus } from "./useChatStream";

export function ChatPage() {
  const [question, setQuestion] = useState("");
  const [selectedCitation, setSelectedCitation] = useState<ChatCitation | null>(null);
  const { sendMessage, state } = useChatStream();
  const isBusy = state.status === "submitting" || state.status === "streaming";

  async function handleSend() {
    setSelectedCitation(null);
    await sendMessage(question);
  }

  return (
    <div className="grid gap-4">
      <ChatComposer
        isBusy={isBusy}
        onChange={setQuestion}
        onSend={() => void handleSend()}
        question={question}
      />

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="grid gap-4">
          {state.retrievalRunId ? (
            <RetrievalRunPanel
              results={state.results}
              retrievalRunId={state.retrievalRunId}
            />
          ) : null}

          {state.answer || state.error ? (
            <MessageList answer={state.answer} error={state.error} status={state.status} />
          ) : null}

          {state.citations.length ? (
            <CitationPanel
              citations={state.citations}
              onSelect={setSelectedCitation}
              selectedKey={selectedCitation?.key ?? null}
            />
          ) : null}

          {state.messageId && state.status === "completed" ? (
            <FeedbackDialog targetId={state.messageId} targetType="chat_message" />
          ) : null}
        </div>

        <aside className="rounded-md border border-[#dcded8] bg-white p-4">
          <h2 className="mb-3 text-base font-semibold">Citation source</h2>
          {selectedCitation ? (
            <SourceLocatorPanel source={sourceFromCitation(selectedCitation)} />
          ) : (
            <p className="text-sm text-[#5d645d]">Select a citation to inspect its source locator.</p>
          )}
        </aside>
      </div>
    </div>
  );
}

function ChatComposer({
  isBusy,
  onChange,
  onSend,
  question,
}: {
  isBusy: boolean;
  onChange: (question: string) => void;
  onSend: () => void;
  question: string;
}) {
  return (
    <section className="rounded-md border border-[#dcded8] bg-white p-4">
      <div className="mb-3 flex items-center justify-between">
        <h1 className="text-lg font-semibold">Chat</h1>
        <MessageSquareText aria-hidden="true" className="text-[#275a53]" size={20} />
      </div>
      <label className="grid gap-2 text-sm font-semibold">
        Chat question
        <textarea
          className="min-h-24 rounded-md border border-[#dcded8] p-3 font-normal"
          onChange={(event) => onChange(event.target.value)}
          value={question}
        />
      </label>
      <button
        className="mt-3 inline-flex items-center gap-2 rounded-md bg-[#123d37] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
        disabled={isBusy}
        onClick={onSend}
        type="button"
      >
        <Send aria-hidden="true" size={16} />
        Send question
      </button>
    </section>
  );
}

function RetrievalRunPanel({
  results,
  retrievalRunId,
}: {
  results: SearchResult[];
  retrievalRunId: string;
}) {
  return (
    <section className="rounded-md border border-[#dcded8] bg-white p-4">
      <div className="mb-2 text-sm font-semibold">Retrieval run</div>
      <div className="rounded-md border border-[#dcded8] px-2 py-1 text-sm">{retrievalRunId}</div>
      {results.map((result) => (
        <p className="mt-2 text-sm text-[#5d645d]" key={result.result_id}>
          {result.title}: {result.preview_text}
        </p>
      ))}
    </section>
  );
}

function MessageList({
  answer,
  error,
  status,
}: {
  answer: string;
  error: string | null;
  status: ChatStreamStatus;
}) {
  return (
    <section className="rounded-md border border-[#dcded8] bg-white p-4">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-base font-semibold">Answer</h2>
        <span className="rounded-md border border-[#dcded8] px-2 py-1 text-xs">{status}</span>
      </div>
      {error ? <p className="text-sm text-[#9a3412]">{error}</p> : null}
      {answer ? <p className="whitespace-pre-wrap text-sm">{answer}</p> : null}
    </section>
  );
}

function CitationPanel({
  citations,
  onSelect,
  selectedKey,
}: {
  citations: ChatCitation[];
  onSelect: (citation: ChatCitation) => void;
  selectedKey: string | null;
}) {
  return (
    <section className="rounded-md border border-[#dcded8] bg-white p-4">
      <h2 className="mb-3 text-base font-semibold">Citations</h2>
      <div className="grid gap-3">
        {citations.map((citation) => (
          <button
            aria-pressed={selectedKey === citation.key}
            className="grid gap-2 rounded-md border border-[#dcded8] p-3 text-left transition hover:border-[#275a53] aria-pressed:border-[#275a53] aria-pressed:bg-[#f0f6f3]"
            key={citation.key}
            onClick={() => onSelect(citation)}
            type="button"
          >
            <span className="w-fit rounded-md bg-[#e1ebe7] px-2 py-1 text-xs font-semibold text-[#123d37]">
              {citation.key}
            </span>
            <span className="text-sm text-[#30342f]">{citation.preview_text}</span>
          </button>
        ))}
      </div>
    </section>
  );
}

function sourceFromCitation(citation: ChatCitation) {
  return {
    id: citation.source_span_id ?? citation.key,
    file_id: citation.file_id,
    document_block_id: null,
    page_number: null,
    char_start: null,
    char_end: null,
    line_start: 1,
    line_end: 3,
    preview_text: citation.preview_text,
    source_available: citation.source_available,
    source_label: citation.label ?? citation.key,
    source_type: "citation",
  };
}
