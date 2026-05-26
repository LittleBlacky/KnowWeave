"use client";

import { Check, Network } from "lucide-react";
import { useEffect, useState } from "react";

import { SourceLocatorPanel } from "@/features/source-viewer/SourceLocatorPanel";
import {
  getKnowledgeUnit,
  listKnowledgeUnits,
  updateKnowledgeUnit,
  type KnowledgeUnit,
  type KnowledgeUnitDetail,
} from "@/shared/api/knowweave";

export function KnowledgeUnitPage() {
  const [units, setUnits] = useState<KnowledgeUnit[]>([]);
  const [detail, setDetail] = useState<KnowledgeUnitDetail | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    async function load() {
      const response = await listKnowledgeUnits();
      setUnits(response.items);
    }
    void load();
  }, []);

  async function handleSelect(unitId: string) {
    setDetail(await getKnowledgeUnit(unitId));
  }

  async function handleVerify() {
    if (!detail) {
      return;
    }
    setBusy(true);
    try {
      const sourceChunkIds = detail.sources
        .map((source) => source.chunk_id)
        .filter((chunkId): chunkId is string => Boolean(chunkId));
      const verified = await updateKnowledgeUnit(detail.id, {
        title: detail.title,
        unit_type: detail.unit_type,
        content: detail.content,
        summary: detail.summary,
        status: "verified",
        applicable_scope: detail.applicable_scope,
        tag_ids: detail.tags.map((tag) => tag.id),
        source_chunk_ids: sourceChunkIds,
      });
      setUnits((current) => current.map((unit) => (unit.id === verified.id ? verified : unit)));
      setDetail((current) => (current ? { ...current, ...verified } : null));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(280px,0.45fr)_minmax(0,0.55fr)]">
      <section className="rounded-md border border-[#dcded8] bg-white">
        <div className="flex items-center justify-between border-b border-[#dcded8] px-4 py-3">
          <h1 className="text-lg font-semibold">Knowledge Units</h1>
          <Network aria-hidden="true" className="text-[#275a53]" size={20} />
        </div>
        <div className="grid gap-3 p-4">
          {units.map((unit) => (
            <button
              aria-pressed={detail?.id === unit.id}
              className="rounded-md border border-[#dcded8] p-4 text-left transition hover:border-[#275a53] aria-pressed:border-[#275a53] aria-pressed:bg-[#f0f6f3]"
              key={unit.id}
              onClick={() => void handleSelect(unit.id)}
              type="button"
            >
              <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-semibold">{unit.title}</h2>
                <span className="rounded-md border border-[#dcded8] px-2 py-1 text-xs">
                  {unit.status}
                </span>
              </div>
              <p className="line-clamp-2 text-sm text-[#30342f]">{unit.summary ?? unit.content}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {unit.tags.map((tag) => (
                  <span
                    className="rounded-md bg-[#e1ebe7] px-2 py-1 text-xs font-semibold text-[#123d37]"
                    key={tag.id}
                  >
                    {tag.name}
                  </span>
                ))}
              </div>
            </button>
          ))}
        </div>
      </section>

      <section className="rounded-md border border-[#dcded8] bg-white">
        <div className="flex items-center justify-between border-b border-[#dcded8] px-4 py-3">
          <h2 className="text-base font-semibold">Unit Detail</h2>
          <button
            className="inline-flex items-center gap-2 rounded-md bg-[#123d37] px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
            disabled={!detail || busy}
            onClick={() => void handleVerify()}
            type="button"
          >
            <Check aria-hidden="true" size={16} />
            Verify knowledge unit
          </button>
        </div>
        {detail ? (
          <div className="grid gap-4 p-4">
            <div>
              <div className="mb-1 text-xs font-semibold uppercase text-[#6f756f]">
                {detail.unit_type} / {detail.created_from}
              </div>
              <h3 className="text-lg font-semibold">{detail.title}</h3>
              <p className="mt-2 text-sm text-[#30342f]">{detail.content}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-md border border-[#dcded8] px-2 py-1 text-xs">
                Status: {detail.status}
              </span>
              {detail.applicable_scope ? (
                <span className="rounded-md border border-[#dcded8] px-2 py-1 text-xs">
                  {detail.applicable_scope}
                </span>
              ) : null}
            </div>
            <div className="grid gap-3">
              {detail.sources.map((source) => (
                <div className="grid gap-2" key={source.id}>
                  <span className="text-sm font-semibold">{source.source_label}</span>
                  <SourceLocatorPanel
                    source={{
                      id: source.source_span_id ?? source.id,
                      file_id: source.file_id,
                      document_block_id: null,
                      page_number: null,
                      char_start: null,
                      char_end: null,
                      line_start: 1,
                      line_end: 3,
                      preview_text: `Evidence: ${detail.content}`,
                      source_available: source.source_available,
                      source_label: source.file_id,
                      source_type: source.source_type,
                    }}
                  />
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="p-4 text-sm text-[#5d645d]">
            Select a Knowledge Unit to inspect sources and governance state.
          </p>
        )}
      </section>
    </div>
  );
}
