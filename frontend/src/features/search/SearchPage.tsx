"use client";

import { Search } from "lucide-react";
import { useState } from "react";

import { SourceLocatorPanel } from "@/features/source-viewer/SourceLocatorPanel";
import { searchKnowledge, type SearchResponse, type SearchResult } from "@/shared/api/knowweave";

export function SearchPage() {
  const [query, setQuery] = useState("approval");
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSearch() {
    setBusy(true);
    try {
      const response = await searchKnowledge(query, 10);
      setResult(response);
      setSelectedResult(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-4">
      <section className="rounded-md border border-[#dcded8] bg-white p-4">
        <div className="mb-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold">Search Evidence</h1>
          <Search aria-hidden="true" className="text-[#275a53]" size={20} />
        </div>
        <div className="grid grid-cols-[minmax(0,1fr)_auto] gap-2 max-sm:grid-cols-1">
          <label className="grid gap-2 text-sm font-semibold">
            Search query
            <input
              className="rounded-md border border-[#dcded8] px-3 py-2 font-normal"
              onChange={(event) => setQuery(event.target.value)}
              value={query}
            />
          </label>
          <button
            className="self-end rounded-md bg-[#123d37] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
            disabled={busy}
            onClick={() => void handleSearch()}
            type="button"
          >
            Run search
          </button>
        </div>
      </section>

      {result ? (
        <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div className="rounded-md border border-[#dcded8] bg-white">
            <div className="flex items-center justify-between border-b border-[#dcded8] px-4 py-3">
              <h2 className="text-base font-semibold">Results</h2>
              <span className="rounded-md border border-[#dcded8] px-2 py-1 text-xs">
                {result.retrieval_run_id}
              </span>
            </div>
            <div className="grid gap-3 p-4">
              {result.results.map((item) => (
                <SearchResultCard
                  isSelected={selectedResult?.result_id === item.result_id}
                  item={item}
                  key={item.result_id}
                  onSelect={() => setSelectedResult(item)}
                />
              ))}
            </div>
          </div>

          <aside className="rounded-md border border-[#dcded8] bg-white p-4">
            <h2 className="mb-3 text-base font-semibold">Retrieval run panel</h2>
            {selectedResult ? (
              <SourceLocatorPanel source={sourceFromSearchResult(selectedResult)} />
            ) : (
              <p className="text-sm text-[#5d645d]">Select a result to inspect its source locator.</p>
            )}
          </aside>
        </section>
      ) : null}
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
      className="grid gap-3 rounded-md border border-[#dcded8] p-4 text-left transition hover:border-[#275a53] aria-pressed:border-[#275a53] aria-pressed:bg-[#f0f6f3]"
      onClick={onSelect}
      type="button"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="text-sm text-[#6f756f]">{item.result_type}</div>
          <h3 className="text-base font-semibold">{item.title}</h3>
        </div>
        <span className="rounded-md bg-[#e1ebe7] px-2 py-1 text-xs font-semibold text-[#123d37]">
          rank {item.rank} / score {item.score}
        </span>
      </div>
      <p className="text-sm text-[#30342f]">{item.preview_text}</p>
      <div className="text-xs font-semibold text-[#275a53]">Inspect source locator</div>
    </button>
  );
}

function sourceFromSearchResult(item: SearchResult) {
  return {
    id: item.source.source_span_id ?? item.result_id,
    document_block_id: null,
    page_number: item.source.page_number,
    char_start: null,
    char_end: null,
    line_start: item.source.line_start,
    line_end: item.source.line_end,
    preview_text: item.preview_text,
  };
}
