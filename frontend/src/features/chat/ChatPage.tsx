"use client";

import { MessageSquareText, Send } from "lucide-react";
import { useState } from "react";

import { FeedbackDialog } from "@/features/feedback/FeedbackDialog";
import { SourceLocatorPanel } from "@/features/source-viewer/SourceLocatorPanel";
import type { SearchResult } from "@/shared/api/knowweave";
import { Badge } from "@/shared/ui";

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

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
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

        <aside className="rounded-lg border border-[#dcded8] bg-white p-4">
          <h2 className="mb-3 text-sm font-semibold text-[#6f756f]">引用来源</h2>
          {selectedCitation ? (
            <SourceLocatorPanel source={sourceFromCitation(selectedCitation)} />
          ) : (
            <p className="text-sm text-[#b0b6ad]">选择一个引用查看来源定位</p>
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
  const canSend = question.trim().length > 0 && !isBusy;

  return (
    <section className="rounded-lg border border-[#dcded8] bg-white p-5">
      <div className="mb-3 flex items-center gap-2">
        <MessageSquareText aria-hidden="true" className="text-[#275a53]" size={20} />
        <h2 className="text-base font-semibold">AI 问答</h2>
      </div>
      <label className="grid gap-2 text-sm font-semibold">
        输入问题
        <textarea
          className="min-h-24 resize-y rounded-lg border border-[#dcded8] p-3 font-normal focus:border-[#275a53] focus:outline-none"
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              canSend && onSend();
            }
          }}
          placeholder="向知识库提问…"
          value={question}
        />
      </label>
      <div className="mt-3 flex items-center justify-between">
        <span className="text-xs text-[#b0b6ad]">Enter 发送 / Shift+Enter 换行</span>
        <button
          className="inline-flex items-center gap-2 rounded-lg bg-[#123d37] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#0e2f2a] disabled:opacity-50"
          disabled={!canSend}
          onClick={onSend}
          type="button"
        >
          <Send aria-hidden="true" size={16} />
          发送
        </button>
      </div>
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
    <section className="rounded-lg border border-[#dcded8] bg-white p-4">
      <div className="mb-2 flex items-center gap-2">
        <span className="text-sm font-semibold">检索结果</span>
        <span className="rounded bg-[#f0f2ed] px-2 py-0.5 text-xs text-[#6f756f]">
          {retrievalRunId.slice(0, 8)}
        </span>
      </div>
      <div className="grid gap-2">
        {results.map((result) => (
          <div
            key={result.result_id}
            className="rounded-lg border border-[#dcded8] bg-[#f7f7f5] p-3"
          >
            <span className="text-sm font-semibold">{result.title}</span>
            <p className="mt-1 line-clamp-2 text-xs text-[#5d645d]">{result.preview_text}</p>
          </div>
        ))}
      </div>
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
    <section className="rounded-lg border border-[#dcded8] bg-white p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold">回答</h2>
        <Badge tone={status === "completed" ? "accent" : "neutral"}>{status}</Badge>
      </div>
      {error ? (
        <p className="rounded-lg border border-[#e8c8c5] bg-[#fdf4f3] p-3 text-sm text-[#a23b35]">
          {error}
        </p>
      ) : null}
      {answer ? (
        <div className="whitespace-pre-wrap text-sm leading-relaxed">{answer}</div>
      ) : null}
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
    <section className="rounded-lg border border-[#dcded8] bg-white p-4">
      <h2 className="mb-3 text-base font-semibold">引用</h2>
      <div className="grid gap-2">
        {citations.map((citation) => (
          <button
            aria-pressed={selectedKey === citation.key}
            key={citation.key}
            className="grid gap-1.5 rounded-lg border border-[#dcded8] p-3 text-left transition hover:border-[#275a53] aria-pressed:border-[#275a53] aria-pressed:bg-[#f0f6f3]"
            onClick={() => onSelect(citation)}
            type="button"
          >
            <Badge tone="accent">{citation.key}</Badge>
            <p className="line-clamp-2 text-sm text-[#30342f]">{citation.preview_text}</p>
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
