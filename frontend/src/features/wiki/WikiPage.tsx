"use client";

import {
  BookOpenCheck,
  History,
  Lightbulb,
  MessageSquareText,
  Plus,
  RotateCcw,
  Save,
} from "lucide-react";
import { useEffect, useState } from "react";

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

type Tab = "editor" | "revisions" | "topic" | "faq";

export function WikiPage() {
  const [pages, setPages] = useState<Wiki[]>([]);
  const [selected, setSelected] = useState<Wiki | null>(null);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [draft, setDraft] = useState("");
  const [changeSummary, setChangeSummary] = useState("");
  const [busy, setBusy] = useState(false);

  // Revisions
  const [revisions, setRevisions] = useState<WikiRevision[]>([]);
  const [activeTab, setActiveTab] = useState<Tab>("editor");

  // Topic Wiki form
  const [topicTheme, setTopicTheme] = useState("");
  const [topicFileIds, setTopicFileIds] = useState("");

  // FAQ Wiki
  const [faqFileId, setFaqFileId] = useState("");

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
      const fileIds = topicFileIds
        .split(/[,;\s]+/)
        .filter(Boolean);
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

  const revisionSourceLabel = (s: string) => {
    switch (s) {
      case "ai_generated": return "AI 生成";
      case "ai_regenerated": return "AI 重新生成";
      case "rollback": return "回滚";
      default: return "人工编辑";
    }
  };

  return (
    <div className="grid gap-4">
      {/* Action bar: Topic / FAQ create */}
      <div className="flex flex-wrap gap-3">
        <div className="flex items-center gap-2 rounded-md border border-[#dcded8] bg-white px-3 py-2">
          <Lightbulb aria-hidden="true" className="text-[#275a53]" size={16} />
          <input
            className="min-w-40 bg-transparent text-sm outline-none"
            onChange={(e) => setTopicTheme(e.target.value)}
            placeholder="主题名称"
            value={topicTheme}
          />
          <input
            className="w-32 bg-transparent text-xs text-[#6f756f] outline-none"
            onChange={(e) => setTopicFileIds(e.target.value)}
            placeholder="文件ID (逗号分隔)"
            value={topicFileIds}
          />
          <button
            className="rounded bg-[#123d37] px-3 py-1 text-xs font-semibold text-white disabled:opacity-50"
            disabled={busy || !topicTheme.trim()}
            onClick={() => void handleCreateTopic()}
            type="button"
          >
            <Plus aria-hidden="true" size={12} className="inline mr-1" />
            创建主题 Wiki
          </button>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-[#dcded8] bg-white px-3 py-2">
          <MessageSquareText aria-hidden="true" className="text-[#275a53]" size={16} />
          <input
            className="w-64 bg-transparent text-sm outline-none"
            onChange={(e) => setFaqFileId(e.target.value)}
            placeholder="文件 ID"
            value={faqFileId}
          />
          <button
            className="rounded bg-[#123d37] px-3 py-1 text-xs font-semibold text-white disabled:opacity-50"
            disabled={busy || !faqFileId.trim()}
            onClick={() => void handleCreateFaq()}
            type="button"
          >
            <Plus aria-hidden="true" size={12} className="inline mr-1" />
            创建 FAQ Wiki
          </button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(280px,0.35fr)_minmax(0,0.65fr)]">
        {/* Left: Wiki list */}
        <section className="rounded-md border border-[#dcded8] bg-white">
          <div className="flex items-center justify-between border-b border-[#dcded8] px-4 py-3">
            <h1 className="text-lg font-semibold">Wiki</h1>
            <BookOpenCheck aria-hidden="true" className="text-[#275a53]" size={20} />
          </div>
          <div className="grid gap-3 p-4">
            {pages.map((page) => (
              <button
                aria-pressed={selected?.id === page.id}
                className="rounded-md border border-[#dcded8] p-4 text-left transition hover:border-[#275a53] aria-pressed:border-[#275a53] aria-pressed:bg-[#f0f6f3]"
                key={page.id}
                onClick={() => void handleSelect(page.id)}
                type="button"
              >
                <div className="mb-2 flex items-center justify-between gap-2">
                  <h2 className="font-semibold">{page.title}</h2>
                  <span className="rounded-md border border-[#dcded8] px-2 py-1 text-xs">
                    {page.status}
                  </span>
                </div>
                <p className="line-clamp-2 text-sm text-[#30342f]">{page.summary}</p>
                <span className="mt-2 inline-block text-xs text-[#6f756f]">
                  {page.wiki_type === "topic_wiki" ? "主题" : page.wiki_type === "faq_wiki" ? "FAQ" : "文档"}
                </span>
              </button>
            ))}
          </div>
        </section>

        {/* Right: Editor / Revisions */}
        <section className="rounded-md border border-[#dcded8] bg-white">
          {/* Tab bar */}
          <div className="flex border-b border-[#dcded8]">
            {(["editor", "revisions"] as Tab[]).map((tab) => (
              <button
                key={tab}
                className={`px-4 py-3 text-sm font-semibold ${activeTab === tab ? "border-b-2 border-[#123d37] text-[#123d37]" : "text-[#6f756f]"}`}
                onClick={() => setActiveTab(tab)}
                type="button"
              >
                {tab === "editor" ? (
                  <><Save size={14} className="inline mr-1" />编辑</>
                ) : (
                  <><History size={14} className="inline mr-1" />版本历史 ({revisions.length})</>
                )}
              </button>
            ))}
          </div>

          {activeTab === "editor" ? (
            <div>
              <div className="flex items-center justify-between border-b border-[#dcded8] px-4 py-3">
                <h2 className="text-base font-semibold">Wiki 编辑器</h2>
                <button
                  className="inline-flex items-center gap-2 rounded-md bg-[#123d37] px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
                  disabled={!selected || !changeSummary.trim() || busy}
                  onClick={() => void handleSave()}
                  type="button"
                >
                  <Save aria-hidden="true" size={16} />
                  保存
                </button>
              </div>
              {selected ? (
                <div className="grid gap-4 p-4">
                  <div className="flex flex-wrap gap-2">
                    <span className="rounded-md border border-[#dcded8] px-2 py-1 text-xs">{selected.wiki_type}</span>
                    <span className="rounded-md border border-[#dcded8] px-2 py-1 text-xs">状态: {selected.status}</span>
                  </div>
                  <label className="grid gap-2 text-sm font-semibold">
                    Markdown 正文
                    <textarea
                      className="min-h-44 resize-y rounded-md border border-[#dcded8] p-3 font-mono text-sm font-normal"
                      onChange={(event) => setDraft(event.target.value)}
                      value={draft}
                    />
                  </label>
                  <label className="grid gap-2 text-sm font-semibold">
                    变更说明
                    <input
                      className="rounded-md border border-[#dcded8] px-3 py-2 font-normal"
                      onChange={(event) => setChangeSummary(event.target.value)}
                      value={changeSummary}
                    />
                  </label>
                  {citations.map((citation) => (
                    <div className="grid gap-2 rounded-md border border-[#dcded8] p-3" key={citation.id}>
                      <span className="text-sm font-semibold">{citation.label}</span>
                      <p className="text-xs text-[#6f756f] line-clamp-2">{citation.preview_text}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="p-4 text-sm text-[#5d645d]">选择一个 Wiki 页面进行编辑。</p>
              )}
            </div>
          ) : (
            <div>
              {revisions.length === 0 ? (
                <p className="p-4 text-sm text-[#5d645d]">暂无版本记录。</p>
              ) : (
                <div className="divide-y divide-[#dcded8]">
                  {revisions.map((rev) => (
                    <div className="flex items-start justify-between gap-4 px-4 py-3" key={rev.id}>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-semibold">v{rev.revision_number}</span>
                          <span className="rounded bg-[#f0f2ed] px-2 py-0.5 text-xs text-[#6f756f]">
                            {revisionSourceLabel(rev.edit_source)}
                          </span>
                          <span className="text-xs text-[#6f756f]">{rev.status}</span>
                        </div>
                        <p className="text-xs text-[#6f756f] truncate">{rev.change_summary}</p>
                        <p className="text-xs text-[#6f756f] mt-1">
                          {new Date(rev.created_at).toLocaleString()}
                        </p>
                      </div>
                      <button
                        className="inline-flex items-center gap-1 rounded border border-[#dcded8] px-2 py-1 text-xs font-semibold text-[#123d37] hover:bg-[#f0f2ed] disabled:opacity-50"
                        disabled={busy}
                        onClick={() => void handleRollback(rev.id)}
                        type="button"
                      >
                        <RotateCcw aria-hidden="true" size={12} />
                        回滚
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
