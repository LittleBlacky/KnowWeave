"use client";

import {
  BookOpenCheck,
  Flag,
  History,
  Lightbulb,
  MessageSquareText,
  Plus,
  RotateCcw,
  Save,
} from "lucide-react";
import {useEffect, useState} from "react";

import {
  createFaqWiki,
  createTopicWiki,
  getWiki,
  listWikiCitations,
  listWikiPages,
  listWikiRevisions,
  rollbackWiki,
  updateWiki,
  type Citation,
  type Wiki,
  type WikiRevision,
} from "@/shared/api/knowweave";
import {
  ListPanel,
  DetailPanel,
  ListItemCard,
  Badge,
  EmptyState,
} from "@/shared/ui";
import {FeedbackDialog} from "@/features/feedback/FeedbackDialog";

type Tab = "editor" | "revisions";

export function WikiPage() {
  const [pages, setPages] = useState<Wiki[]>([]);
  const [selected, setSelected] = useState<Wiki | null>(null);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [draft, setDraft] = useState("");
  const [changeSummary, setChangeSummary] = useState("");
  const [busy, setBusy] = useState(false);

  const [revisions, setRevisions] = useState<WikiRevision[]>([]);
  const [activeTab, setActiveTab] = useState<Tab>("editor");

  const [topicTheme, setTopicTheme] = useState("");
  const [topicFileIds, setTopicFileIds] = useState("");

  const [faqFileId, setFaqFileId] = useState("");
  const [showFeedback, setShowFeedback] = useState(false);

  useEffect(() => {
    async function loadPages() {
      const response = await listWikiPages();
      setPages(response.items);
    }
    void loadPages();
  }, []);

  async function handleSelect(wikiId: string) {
    const [wiki, citationResponse, revs] = await Promise.all([
      getWiki(wikiId),
      listWikiCitations(wikiId),
      listWikiRevisions(wikiId),
    ]);
    setSelected(wiki);
    setDraft(wiki.content_markdown);
    setChangeSummary("");
    setCitations(citationResponse.items);
    setRevisions(Array.isArray(revs) ? revs : []);
    setActiveTab("editor");
  }

  async function handleSave() {
    if (!selected || !changeSummary.trim()) return;
    setBusy(true);
    try {
      const updated = await updateWiki(selected.id, {
        title: selected.title,
        content_markdown: draft,
        change_summary: changeSummary,
        status: selected.status,
        summary: selected.summary,
      });
      setSelected(updated);
      setDraft(updated.content_markdown);
      setPages((c) => c.map((p) => (p.id === updated.id ? updated : p)));
      handleSelect(updated.id);
    } finally {
      setBusy(false);
    }
  }

  async function handleRollback(revId: string) {
    if (!selected) return;
    setBusy(true);
    try {
      const rolled = await rollbackWiki(selected.id, revId);
      setSelected(rolled);
      setDraft(rolled.content_markdown);
      handleSelect(rolled.id);
    } finally {
      setBusy(false);
    }
  }

  async function handleCreateTopic() {
    if (!topicTheme.trim()) return;
    setBusy(true);
    try {
      const fileIds = topicFileIds.split(/[,;\s]+/).filter(Boolean);
      await createTopicWiki({
        theme: topicTheme,
        file_ids: fileIds.length > 0 ? fileIds : undefined,
      });
      setTopicTheme("");
      setTopicFileIds("");
      const response = await listWikiPages();
      setPages(response.items);
    } finally {
      setBusy(false);
    }
  }

  async function handleCreateFaq() {
    if (!faqFileId.trim()) return;
    setBusy(true);
    try {
      await createFaqWiki(faqFileId.trim());
      setFaqFileId("");
      const response = await listWikiPages();
      setPages(response.items);
    } finally {
      setBusy(false);
    }
  }

  const wikiTypeLabel = (t: string) =>
    t === "topic_wiki" ? "主题" : t === "faq_wiki" ? "FAQ" : "文档";

  const revisionSourceLabel = (s: string) => {
    switch (s) {
      case "ai_generated":
        return "AI 生成";
      case "ai_regenerated":
        return "AI 重新生成";
      case "rollback":
        return "回滚";
      default:
        return "人工编辑";
    }
  };

  return (
    <div className="grid gap-4">
      {/* Quick-create bar */}
      <div className="flex flex-wrap gap-3 rounded-lg border border-[#dcded8] bg-white p-3">
        <div className="flex flex-1 flex-wrap items-center gap-2 min-w-0">
          <Lightbulb aria-hidden="true" className="text-[#275a53]" size={16} />
          <input
            className="min-w-32 flex-1 bg-transparent text-sm outline-none"
            onChange={(e) => setTopicTheme(e.target.value)}
            placeholder="主题名称"
            value={topicTheme}
          />
          <input
            className="w-40 bg-transparent text-xs text-[#6f756f] outline-none"
            onChange={(e) => setTopicFileIds(e.target.value)}
            placeholder="文件ID (逗号分隔)"
            value={topicFileIds}
          />
          <button
            className="shrink-0 rounded-lg bg-[#123d37] px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-[#0e2f2a] disabled:opacity-50"
            disabled={busy || !topicTheme.trim()}
            onClick={() => void handleCreateTopic()}
            type="button"
          >
            <Plus aria-hidden="true" size={12} className="inline mr-1" />
            创建主题 Wiki
          </button>
        </div>
        <div className="flex flex-1 flex-wrap items-center gap-2 min-w-0">
          <MessageSquareText
            aria-hidden="true"
            className="text-[#275a53]"
            size={16}
          />
          <input
            className="min-w-32 flex-1 bg-transparent text-sm outline-none"
            onChange={(e) => setFaqFileId(e.target.value)}
            placeholder="文件 ID"
            value={faqFileId}
          />
          <button
            className="shrink-0 rounded-lg bg-[#123d37] px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-[#0e2f2a] disabled:opacity-50"
            disabled={busy || !faqFileId.trim()}
            onClick={() => void handleCreateFaq()}
            type="button"
          >
            <Plus aria-hidden="true" size={12} className="inline mr-1" />
            创建 FAQ Wiki
          </button>
        </div>
      </div>

      {/* List + Detail */}
      <div className="grid gap-4 lg:grid-cols-[minmax(320px,0.38fr)_minmax(0,0.62fr)]">
        <ListPanel title="Wiki 列表" icon={BookOpenCheck} count={pages.length}>
          <div className="grid gap-2.5">
            {pages.map((page) => (
              <ListItemCard
                key={page.id}
                active={selected?.id === page.id}
                onClick={() => void handleSelect(page.id)}
                title={page.title}
                subtitle={page.summary ?? undefined}
                status={page.status}
                tags={[
                  {id: page.wiki_type, name: wikiTypeLabel(page.wiki_type)},
                ]}
              />
            ))}
          </div>
        </ListPanel>

        <DetailPanel title={selected ? undefined : "Wiki 详情"}>
          {!selected ? (
            <EmptyState
              icon={BookOpenCheck}
              title="选择 Wiki 页面"
              description="从左侧列表选择一个页面进行编辑或查看版本历史。"
            />
          ) : (
            <div>
              {/* Tabs */}
              <div className="-mx-4 -mt-4 mb-4 flex border-b border-[#dcded8]">
                {(["editor", "revisions"] as Tab[]).map((tab) => (
                  <button
                    key={tab}
                    className={`px-4 py-2.5 text-sm font-semibold transition ${
                      activeTab === tab
                        ? "border-b-2 border-[#123d37] text-[#123d37]"
                        : "text-[#6f756f] hover:text-[#30342f]"
                    }`}
                    onClick={() => setActiveTab(tab)}
                    type="button"
                  >
                    {tab === "editor" ? (
                      <>
                        <Save size={14} className="inline mr-1.5" />
                        编辑
                      </>
                    ) : (
                      <>
                        <History size={14} className="inline mr-1.5" />
                        版本 ({revisions.length})
                      </>
                    )}
                  </button>
                ))}
              </div>

              {activeTab === "editor" ? (
                <div className="grid gap-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge>{selected.wiki_type}</Badge>
                    <Badge
                      tone={
                        selected.status === "published" ? "accent" : "neutral"
                      }
                    >
                      {selected.status}
                    </Badge>
                  </div>

                  <label className="grid gap-1.5 text-sm font-semibold">
                    Markdown 正文
                    <textarea
                      className="min-h-52 resize-y rounded-lg border border-[#dcded8] p-3 font-mono text-sm font-normal focus:border-[#275a53] focus:outline-none"
                      onChange={(e) => setDraft(e.target.value)}
                      value={draft}
                    />
                  </label>

                  <label className="grid gap-1.5 text-sm font-semibold">
                    变更说明
                    <input
                      className="rounded-lg border border-[#dcded8] px-3 py-2 font-normal focus:border-[#275a53] focus:outline-none"
                      onChange={(e) => setChangeSummary(e.target.value)}
                      placeholder="简述本次修改内容"
                      value={changeSummary}
                    />
                  </label>

                  <button
                    className="inline-flex items-center gap-2 self-start rounded-lg bg-[#123d37] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#0e2f2a] disabled:opacity-50"
                    disabled={!changeSummary.trim() || busy}
                    onClick={() => void handleSave()}
                    type="button"
                  >
                    <Save aria-hidden="true" size={16} />
                    保存修改
                  </button>

                  <button
                    className="inline-flex items-center gap-2 self-start rounded-lg border border-[#dcded8] px-4 py-2 text-sm font-semibold text-[#6f756f] transition hover:border-[#a23b35] hover:text-[#a23b35]"
                    onClick={() => setShowFeedback((v) => !v)}
                    type="button"
                  >
                    <Flag aria-hidden="true" size={16} />
                    反馈
                  </button>

                  {showFeedback && selected && (
                    <FeedbackDialog
                      targetId={selected.id}
                      targetType="wiki_page"
                    />
                  )}

                  {citations.length > 0 && (
                    <div className="grid gap-2">
                      <h3 className="text-sm font-semibold text-[#6f756f]">
                        引用来源
                      </h3>
                      {citations.map((c) => (
                        <div
                          key={c.id}
                          className="rounded-lg border border-[#dcded8] bg-[#f0f6f3] p-3"
                        >
                          <span className="text-sm font-semibold">
                            {c.label}
                          </span>
                          <p className="mt-1 line-clamp-2 text-xs text-[#5d645d]">
                            {c.preview_text}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  {revisions.length === 0 ? (
                    <p className="py-8 text-center text-sm text-[#6f756f]">
                      暂无版本记录
                    </p>
                  ) : (
                    <div className="divide-y divide-[#dcded8]">
                      {revisions.map((rev) => (
                        <div
                          key={rev.id}
                          className="flex items-start justify-between gap-4 py-3"
                        >
                          <div className="min-w-0 flex-1">
                            <div className="mb-1 flex flex-wrap items-center gap-2">
                              <span className="text-sm font-semibold">
                                v{rev.revision_number}
                              </span>
                              <Badge tone="accent">
                                {revisionSourceLabel(rev.edit_source)}
                              </Badge>
                            </div>
                            <p className="truncate text-xs text-[#5d645d]">
                              {rev.change_summary || "无变更说明"}
                            </p>
                            <p className="mt-0.5 text-xs text-[#b0b6ad]">
                              {new Date(rev.created_at).toLocaleString()}
                            </p>
                          </div>
                          <button
                            className="shrink-0 rounded border border-[#dcded8] px-2.5 py-1 text-xs font-semibold text-[#123d37] transition hover:bg-[#f0f2ed] disabled:opacity-50"
                            disabled={busy}
                            onClick={() => void handleRollback(rev.id)}
                            type="button"
                          >
                            <RotateCcw
                              aria-hidden="true"
                              size={12}
                              className="inline mr-1"
                            />
                            回滚
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </DetailPanel>
      </div>
    </div>
  );
}
