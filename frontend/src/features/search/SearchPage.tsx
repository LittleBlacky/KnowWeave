"use client";

import { Search } from "lucide-react";
import { useState } from "react";

import { SourceLocatorPanel } from "@/features/source-viewer/SourceLocatorPanel";
import { searchKnowledge, type SearchResponse, type SearchResult } from "@/shared/api/knowweave";
import { Badge } from "@/shared/ui";

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [targetTypes, setTargetTypes] = useState([
    "file", "chunk", "knowledge_unit", "wiki_page",
  ]);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSearch() {
    if (!query.trim()) return;
    setBusy(true);
    try {
      const response = await searchKnowledge(query, 10, targetTypes);
      setResult(response);
      setSelectedResult(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-4">
      {/* Search form */}
      <section className="rounded-lg border border-[#dcded8] bg-white p-5">
        <div className="mb-3 flex items-center gap-2">
          <Search aria-hidden="true" className="text-[#275a53]" size={20} />
          <h2 className="text-base font-semibold">搜索知识</h2>
        </div>

        <div className="grid grid-cols-[minmax(0,1fr)_auto] gap-3 max-sm:grid-cols-1">
          <label className="grid gap-1.5 text-sm font-semibold">
            搜索关键词
            <input
              className="rounded-lg border border-[#dcded8] px-3 py-2.5 font-normal focus:border-[#275a53] focus:outline-none"
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleSearch(); }}
              placeholder="输入关键词搜索知识库…"
              value={query}
            />
          </label>
          <button
            className="self-end rounded-lg bg-[#123d37] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#0e2f2a] disabled:opacity-50"
            disabled={busy || !query.trim()}
            onClick={() => void handleSearch()}
            type="button"
          >
            {busy ? "搜索中…" : "搜索"}
          </button>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-4">
          <span className="text-xs font-semibold text-[#6f756f]">搜索范围:</span>
          {[
            ["file", "文件"],
            ["chunk", "分块"],
            ["knowledge_unit", "知识单元"],
            ["wiki_page", "Wiki"],
          ].map(([value, label]) => (
            <label key={value} className="inline-flex items-center gap-1.5 text-sm cursor-pointer">
              <input
                checked={targetTypes.includes(value)}
                className="accent-[#275a53]"
                onChange={(e) => {
                  setTargetTypes((c) =>
                    e.target.checked ? [...c, value] : c.filter((t) => t !== value)
                  );
                }}
                type="checkbox"
              />
              {label}
            </label>
          ))}
        </div>
      </section>

      {/* Results */}
      {result && (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
          <section className="rounded-lg border border-[#dcded8] bg-white">
            <div className="flex items-center justify-between border-b border-[#dcded8] px-4 py-3">
              <h2 className="text-base font-semibold">
                搜索结果 ({result.results.length})
              </h2>
              <span className="rounded bg-[#f0f2ed] px-2 py-0.5 text-xs text-[#6f756f]">
                {result.retrieval_run_id.slice(0, 8)}
              </span>
            </div>
            <div className="grid gap-3 p-4">
              {result.results.map((item) => (
                <SearchResultCard
                  key={item.result_id}
                  isSelected={selectedResult?.result_id === item.result_id}
                  item={item}
                  onSelect={() => setSelectedResult(item)}
                />
              ))}
            </div>
          </section>

          <aside className="rounded-lg border border-[#dcded8] bg-white p-4">
            <h2 className="mb-3 text-sm font-semibold text-[#6f756f]">来源定位</h2>
            {selectedResult ? (
              <SourceLocatorPanel source={sourceFromSearchResult(selectedResult)} />
            ) : (
              <p className="text-sm text-[#b0b6ad]">选择一个结果查看来源定位</p>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}

function SearchResultCard({
  isSelected,
  item,
  onSelect,
}: {
  isSelected: boolean;
  item: SearchResult;
  onSelect: () => void;
}) {
  return (
    <button
      aria-pressed={isSelected}
      className="grid gap-2 rounded-lg border border-[#dcded8] p-4 text-left transition hover:border-[#275a53] aria-pressed:border-[#275a53] aria-pressed:bg-[#f0f6f3]"
      onClick={onSelect}
      type="button"
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <span className="text-xs text-[#6f756f]">{item.result_type}</span>
          <h3 className="text-sm font-semibold">{item.title}</h3>
        </div>
        <div className="flex items-center gap-1.5">
          <Badge tone="accent">#{item.rank}</Badge>
          <span className="text-xs text-[#b0b6ad]">{(Number(item.score) * 100).toFixed(0)}%</span>
        </div>
      </div>
      <p className="line-clamp-2 text-sm text-[#30342f]">{item.preview_text}</p>
    </button>
  );
}

function sourceFromSearchResult(item: SearchResult) {
  return {
    id: item.source.source_span_id ?? item.result_id,
    file_id: item.source.file_id,
    document_block_id: null,
    page_number: item.source.page_number,
    char_start: null,
    char_end: null,
    line_start: item.source.line_start,
    line_end: item.source.line_end,
    preview_text: item.preview_text,
    source_available: item.source.source_available,
    source_label: item.source.file_name ?? item.title,
    source_type: item.result_type,
  };
}
