"use client";

import { BookOpenCheck, Save } from "lucide-react";
import { useEffect, useState } from "react";

import { SourceLocatorPanel } from "@/features/source-viewer/SourceLocatorPanel";
import {
  getWiki,
  listWikiCitations,
  listWikiPages,
  updateWiki,
  type Citation,
  type Wiki,
} from "@/shared/api/knowweave";

export function WikiPage() {
  const [pages, setPages] = useState<Wiki[]>([]);
  const [selected, setSelected] = useState<Wiki | null>(null);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [draft, setDraft] = useState("");
  const [changeSummary, setChangeSummary] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    async function loadPages() {
      const response = await listWikiPages();
      setPages(response.items);
    }
    void loadPages();
  }, []);

  async function handleSelect(wikiId: string) {
    const [wiki, citationResponse] = await Promise.all([
      getWiki(wikiId),
      listWikiCitations(wikiId),
    ]);
    setSelected(wiki);
    setDraft(wiki.content_markdown);
    setChangeSummary("");
    setCitations(citationResponse.items);
  }

  async function handleSave() {
    if (!selected || !changeSummary.trim()) {
      return;
    }
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
      setPages((current) => current.map((page) => (page.id === updated.id ? updated : page)));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(280px,0.42fr)_minmax(0,0.58fr)]">
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
            </button>
          ))}
        </div>
      </section>

      <section className="rounded-md border border-[#dcded8] bg-white">
        <div className="flex items-center justify-between border-b border-[#dcded8] px-4 py-3">
          <h2 className="text-base font-semibold">Wiki Editor</h2>
          <button
            className="inline-flex items-center gap-2 rounded-md bg-[#123d37] px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
            disabled={!selected || !changeSummary.trim() || busy}
            onClick={() => void handleSave()}
            type="button"
          >
            <Save aria-hidden="true" size={16} />
            Save wiki
          </button>
        </div>
        {selected ? (
          <div className="grid gap-4 p-4">
            <div className="flex flex-wrap gap-2">
              <span className="rounded-md border border-[#dcded8] px-2 py-1 text-xs">
                {selected.wiki_type}
              </span>
              <span className="rounded-md border border-[#dcded8] px-2 py-1 text-xs">
                Status: {selected.status}
              </span>
            </div>
            <label className="grid gap-2 text-sm font-semibold">
              Wiki markdown
              <textarea
                className="min-h-44 resize-y rounded-md border border-[#dcded8] p-3 font-mono text-sm font-normal"
                onChange={(event) => setDraft(event.target.value)}
                value={draft}
              />
            </label>
            <label className="grid gap-2 text-sm font-semibold">
              Change summary
              <input
                className="rounded-md border border-[#dcded8] px-3 py-2 font-normal"
                onChange={(event) => setChangeSummary(event.target.value)}
                value={changeSummary}
              />
            </label>
            <div className="grid gap-3">
              {citations.map((citation) => (
                <div className="grid gap-2" key={citation.id}>
                  <span className="text-sm font-semibold">{citation.label}</span>
                  <SourceLocatorPanel
                    source={{
                      id: citation.source_span_id ?? citation.id,
                      file_id: citation.file_id,
                      document_block_id: null,
                      page_number: null,
                      char_start: null,
                      char_end: null,
                      line_start: 1,
                      line_end: 3,
                      preview_text: `Citation ${citation.label ?? citation.id} source span`,
                      source_available: citation.source_available,
                      source_label: citation.file_id,
                      source_type: citation.target_type,
                    }}
                  />
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="p-4 text-sm text-[#5d645d]">Select a wiki page to edit and inspect citations.</p>
        )}
      </section>
    </div>
  );
}
