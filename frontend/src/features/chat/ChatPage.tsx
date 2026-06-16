"use client";

import {
  Bot,
  ChevronDown,
  ChevronUp,
  FlaskConical,
  MessageSquarePlus,
  MessageSquareText,
  PanelRightClose,
  PanelRightOpen,
  Search,
  Send,
  ThumbsDown,
  ThumbsUp,
  Trash2,
  User,
} from "lucide-react";
import {useEffect, useRef, useState} from "react";

import {FeedbackDialog} from "@/features/feedback/FeedbackDialog";
import {SourceLocatorPanel} from "@/features/source-viewer/SourceLocatorPanel";
import {createEvaluationSampleFromChatMessage} from "@/shared/api/knowweave";
import {Badge} from "@/shared/ui";

import {
  useChatStream,
  type ChatCitation,
  type ChatSession,
  type Message,
} from "./useChatStream";

export function ChatPage() {
  const [question, setQuestion] = useState("");
  const [selectedCitation, setSelectedCitation] = useState<ChatCitation | null>(
    null,
  );
  const [sourceOpen, setSourceOpen] = useState(false);
  const {sendMessage, newChat, switchSession, deleteActiveSession, state} =
    useChatStream();
  const isBusy = state.status !== "idle";

  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({behavior: "smooth"});
  }, [state.messages]);

  async function handleSend() {
    const q = question.trim();
    if (!q || isBusy) return;
    setQuestion("");
    setSelectedCitation(null);
    await sendMessage(q);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  }

  const canSend = question.trim().length > 0 && !isBusy;
  const activeSession = state.sessions.find(
    (s) => s.id === state.activeSessionId,
  );

  return (
    <div className="flex h-[calc(100vh-6rem)] gap-0">
      {/* Session sidebar */}
      <aside className="flex w-[260px] shrink-0 flex-col border-r border-[#dcded8] bg-[#f7f7f5]">
        <div className="border-b border-[#dcded8] px-3 py-2.5">
          <button
            className="flex w-full items-center gap-2 rounded-lg border border-[#dcded8] bg-white px-3 py-2 text-sm font-medium transition hover:border-[#275a53] hover:bg-[#f0f6f3]"
            onClick={newChat}
            type="button"
          >
            <MessageSquarePlus size={16} className="text-[#275a53]" />
            新对话
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {state.sessions.length === 0 ? (
            <p className="px-4 py-8 text-center text-xs text-[#b0b6ad]">
              暂无对话记录
            </p>
          ) : (
            <div className="flex flex-col gap-0.5 p-2">
              {state.sessions.map((session) => (
                <SessionItem
                  key={session.id}
                  active={session.id === state.activeSessionId}
                  onDelete={
                    session.id === state.activeSessionId
                      ? deleteActiveSession
                      : undefined
                  }
                  onClick={() => void switchSession(session.id)}
                  session={session}
                />
              ))}
            </div>
          )}
        </div>
      </aside>

      {/* Main chat area */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#dcded8] px-4 py-2">
          <div className="flex items-center gap-2">
            <MessageSquareText
              aria-hidden="true"
              className="text-[#275a53]"
              size={18}
            />
            <span className="text-sm font-semibold">
              {activeSession ? activeSession.title : "AI 问答"}
            </span>
            {isBusy && <span className="text-xs text-[#b0b6ad]">回复中…</span>}
          </div>
          <button
            className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-[#6f756f] hover:bg-[#f0f2ed]"
            onClick={() => setSourceOpen((v) => !v)}
            type="button"
          >
            {sourceOpen ? (
              <PanelRightClose size={14} />
            ) : (
              <PanelRightOpen size={14} />
            )}
            来源
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          {state.messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <div className="mx-auto mb-4 flex size-16 items-center justify-center rounded-full bg-[#f0f6f3]">
                <Bot size={32} className="text-[#275a53]" />
              </div>
              <h3 className="text-lg font-semibold text-[#30342f]">
                知识库 AI 助手
              </h3>
              <p className="mt-2 max-w-md text-sm text-[#6f756f]">
                基于已上传的知识文件，向 AI 提问任何相关问题。
              </p>
            </div>
          ) : (
            <div className="mx-auto max-w-3xl space-y-6">
              {state.messages.map((msg) => (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  onCitationClick={(c) => {
                    setSelectedCitation(c);
                    setSourceOpen(true);
                  }}
                />
              ))}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-[#dcded8] bg-white px-4 py-3">
          <div className="mx-auto flex max-w-3xl items-end gap-3">
            <textarea
              className="min-h-[44px] max-h-32 flex-1 resize-none rounded-lg border border-[#dcded8] px-4 py-2.5 text-sm placeholder:text-[#b0b6ad] focus:border-[#275a53] focus:outline-none"
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="向知识库提问…"
              rows={1}
              value={question}
            />
            <button
              className="inline-flex size-10 shrink-0 items-center justify-center rounded-lg bg-[#123d37] text-white transition hover:bg-[#0e2f2a] disabled:opacity-40"
              disabled={!canSend}
              onClick={() => void handleSend()}
              type="button"
            >
              <Send size={18} />
            </button>
          </div>
          <p className="mx-auto mt-1.5 max-w-3xl text-xs text-[#b0b6ad]">
            Enter 发送 · Shift+Enter 换行
          </p>
        </div>
      </div>

      {/* Source sidebar */}
      {sourceOpen && (
        <aside className="w-80 shrink-0 border-l border-[#dcded8] bg-white">
          <div className="flex items-center justify-between border-b border-[#dcded8] px-4 py-2.5">
            <h3 className="text-sm font-semibold text-[#6f756f]">引用来源</h3>
            <button
              className="rounded p-0.5 text-[#b0b6ad] hover:text-[#30342f]"
              onClick={() => setSourceOpen(false)}
              type="button"
            >
              <PanelRightClose size={16} />
            </button>
          </div>
          <div className="p-3">
            {selectedCitation ? (
              <SourceLocatorPanel
                source={sourceFromCitation(selectedCitation)}
              />
            ) : (
              <p className="text-sm text-[#b0b6ad]">
                点击消息中的引用查看来源定位
              </p>
            )}
          </div>
        </aside>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Session Item                                                        */
/* ------------------------------------------------------------------ */
function SessionItem({
  active,
  onClick,
  onDelete,
  session,
}: {
  active: boolean;
  onClick: () => void;
  onDelete?: () => void;
  session: ChatSession;
}) {
  return (
    <div
      className={`group flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition ${
        active
          ? "bg-white border border-[#dcded8]"
          : "hover:bg-white/60 cursor-pointer"
      }`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter") onClick();
      }}
    >
      <MessageSquareText size={14} className="shrink-0 text-[#b0b6ad]" />
      <span className="flex-1 truncate text-[#30342f]">
        {session.title || "新对话"}
      </span>
      {onDelete && (
        <button
          className="shrink-0 rounded p-0.5 text-[#b0b6ad] opacity-0 transition hover:text-[#a23b35] group-hover:opacity-100"
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          type="button"
          title="删除对话"
        >
          <Trash2 size={14} />
        </button>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Message Bubble                                                      */
/* ------------------------------------------------------------------ */
function MessageBubble({
  message,
  onCitationClick,
}: {
  message: Message;
  onCitationClick: (c: ChatCitation) => void;
}) {
  const isUser = message.role === "user";
  const [showRetrieval, setShowRetrieval] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      {/* Avatar */}
      <div
        className={`flex size-8 shrink-0 items-center justify-center rounded-full ${
          isUser ? "bg-[#275a53] text-white" : "bg-[#f0f2ed] text-[#275a53]"
        }`}
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      {/* Content */}
      <div className={`min-w-0 max-w-[85%] ${isUser ? "text-right" : ""}`}>
        {/* User message: simple chip */}
        {isUser ? (
          <div className="inline-block rounded-2xl rounded-tr-sm bg-[#123d37] px-4 py-2.5 text-sm text-white">
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>
        ) : (
          <div className="space-y-3 rounded-2xl rounded-tl-sm border border-[#dcded8] bg-white px-4 py-3.5">
            {/* Status */}
            {message.status === "pending" && (
              <p className="flex items-center gap-2 text-sm text-[#b0b6ad]">
                <span className="inline-block size-2 animate-pulse rounded-full bg-[#275a53]" />
                检索知识库中…
              </p>
            )}

            {/* Answer */}
            {message.content && (
              <div className="prose prose-sm max-w-none text-sm leading-relaxed whitespace-pre-wrap text-[#30342f]">
                {message.content}
              </div>
            )}

            {/* Streaming indicator */}
            {message.status === "streaming" && !message.content && (
              <span className="inline-block size-2 animate-pulse rounded-full bg-[#275a53]" />
            )}

            {/* Error */}
            {message.error && (
              <p className="rounded-lg border border-[#e8c8c5] bg-[#fdf4f3] px-3 py-2 text-sm text-[#a23b35]">
                {message.error}
              </p>
            )}

            {/* Retrieval panel */}
            {message.retrievalResults.length > 0 && (
              <div>
                <button
                  className="flex items-center gap-1 text-xs text-[#6f756f] hover:text-[#30342f]"
                  onClick={() => setShowRetrieval((v) => !v)}
                  type="button"
                >
                  <Search size={12} />
                  检索到 {message.retrievalResults.length} 条参考资料
                  {showRetrieval ? (
                    <ChevronUp size={12} />
                  ) : (
                    <ChevronDown size={12} />
                  )}
                </button>
                {showRetrieval && (
                  <div className="mt-2 grid gap-1.5">
                    {message.retrievalResults.slice(0, 5).map((r) => (
                      <div
                        key={r.result_id}
                        className="rounded border border-[#dcded8] bg-[#f7f7f5] px-3 py-2 text-xs"
                      >
                        <span className="font-semibold">{r.title}</span>
                        <p className="mt-0.5 line-clamp-1 text-[#5d645d]">
                          {r.preview_text}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Citations */}
            {message.citations.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-xs text-[#b0b6ad]">引用:</span>
                {message.citations.map((c) => (
                  <button
                    key={c.key}
                    className="inline-flex items-center rounded bg-[#f0f6f3] px-2 py-0.5 text-xs font-medium text-[#275a53] transition hover:bg-[#d4e5dd]"
                    onClick={() => onCitationClick(c)}
                    type="button"
                  >
                    {c.key}
                  </button>
                ))}
              </div>
            )}

            {/* Feedback + status */}
            {message.status === "completed" && (
              <div className="flex items-center gap-3 border-t border-[#dcded8] pt-2.5">
                <button
                  className="inline-flex items-center gap-1 text-xs text-[#b0b6ad] hover:text-[#275a53]"
                  onClick={() => setShowFeedback((v) => !v)}
                  type="button"
                >
                  {showFeedback ? (
                    <ThumbsDown size={13} />
                  ) : (
                    <ThumbsUp size={13} />
                  )}
                  反馈
                </button>
                {message.messageId && (
                  <button
                    className="inline-flex items-center gap-1 text-xs text-[#b0b6ad] hover:text-[#275a53]"
                    onClick={async () => {
                      try {
                        await createEvaluationSampleFromChatMessage(
                          message.messageId!,
                        );
                      } catch {
                        /* ignore */
                      }
                    }}
                    type="button"
                  >
                    <FlaskConical size={13} />
                    转为评测
                  </button>
                )}
                {showFeedback && message.messageId && (
                  <FeedbackDialog
                    targetId={message.messageId}
                    targetType="chat_message"
                  />
                )}
                <Badge tone="accent">✓ 已完成</Badge>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */
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
  };
}
