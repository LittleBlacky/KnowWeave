"use client";

import { Check, EyeOff, Save } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  ignoreChunk,
  listFileChunks,
  listFiles,
  updateChunk,
  verifyChunk,
  type Chunk,
} from "@/shared/api/knowweave";
import { SourceLocatorPanel } from "@/features/source-viewer/SourceLocatorPanel";

export function ChunkWorkspace() {
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const selected = useMemo(
    () => chunks.find((chunk) => chunk.id === selectedId) ?? chunks[0],
    [chunks, selectedId],
  );

  useEffect(() => {
    async function load() {
      const files = await listFiles();
      const firstFile = files.items[0];
      if (!firstFile) {
        setChunks([]);
        return;
      }
      const response = await listFileChunks(firstFile.id);
      setChunks(response.items);
      setSelectedId(response.items[0]?.id ?? null);
      setDraft(response.items[0]?.edited_content ?? response.items[0]?.raw_content ?? "");
    }
    void load();
  }, []);

  function replaceChunk(next: Chunk) {
    setChunks((current) => current.map((chunk) => (chunk.id === next.id ? next : chunk)));
    setSelectedId(next.id);
    setDraft(next.edited_content ?? next.raw_content);
  }

  async function handleSave() {
    if (!selected) {
      return;
    }
    replaceChunk(await updateChunk(selected.id, draft));
  }

  async function handleIgnore() {
    if (!selected) {
      return;
    }
    replaceChunk(await ignoreChunk(selected.id));
  }

  async function handleVerify() {
    if (!selected) {
      return;
    }
    replaceChunk(await verifyChunk(selected.id));
  }

  if (!selected) {
    return (
      <section className="rounded-md border border-[#dcded8] bg-white p-6 text-sm text-[#6f756f]">
        No chunks available.
      </section>
    );
  }

  const source = selected.source_spans[0]
    ? { ...selected.source_spans[0], file_id: selected.file_id }
    : undefined;

  return (
    <div className="grid grid-cols-[minmax(260px,0.45fr)_minmax(0,0.55fr)] gap-4 max-xl:grid-cols-1">
      <section className="rounded-md border border-[#dcded8] bg-white">
        <div className="border-b border-[#dcded8] px-4 py-3">
          <h2 className="text-base font-semibold">Chunk Workspace</h2>
        </div>
        <div className="divide-y divide-[#dcded8]">
          {chunks.map((chunk) => (
            <button
              className="block w-full px-4 py-3 text-left hover:bg-[#f0f2ed] data-[selected=true]:bg-[#e1ebe7]"
              data-selected={chunk.id === selected.id}
              key={chunk.id}
              onClick={() => {
                setSelectedId(chunk.id);
                setDraft(chunk.edited_content ?? chunk.raw_content);
              }}
              type="button"
            >
              <div className="mb-2 flex items-center justify-between gap-2">
                <span className="text-sm font-semibold">Chunk {chunk.chunk_index + 1}</span>
                <span className="rounded-md border border-[#dcded8] px-2 py-1 text-xs">
                  {chunk.status}
                </span>
              </div>
              <p className="line-clamp-2 text-sm text-[#30342f]">
                {chunk.edited_content ?? chunk.raw_content}
              </p>
            </button>
          ))}
        </div>
      </section>

      <section className="rounded-md border border-[#dcded8] bg-white">
        <div className="flex items-center justify-between border-b border-[#dcded8] px-4 py-3">
          <h2 className="text-base font-semibold">Chunk Detail</h2>
          {selected.is_manually_edited ? (
            <span className="rounded-md bg-[#e1ebe7] px-2 py-1 text-xs font-semibold text-[#123d37]">
              Edited
            </span>
          ) : null}
        </div>
        <div className="grid gap-4 p-4">
          <div>
            <div className="mb-2 text-sm font-semibold">Raw content</div>
            <p className="rounded-md border border-[#dcded8] bg-[#f7f7f5] p-3 text-sm">
              {selected.raw_content}
            </p>
          </div>
          <label className="grid gap-2 text-sm font-semibold">
            Edited chunk content
            <textarea
              className="min-h-32 resize-y rounded-md border border-[#dcded8] p-3 text-sm font-normal"
              onChange={(event) => setDraft(event.target.value)}
              value={draft}
            />
          </label>
          <SourceLocatorPanel source={source} />
          <div className="flex flex-wrap gap-2">
            <button
              aria-label="Save chunk edits"
              className="inline-flex items-center gap-2 rounded-md bg-[#123d37] px-3 py-2 text-sm font-semibold text-white"
              onClick={() => void handleSave()}
              type="button"
            >
              <Save aria-hidden="true" size={16} />
              Save
            </button>
            <button
              aria-label="Ignore chunk"
              className="inline-flex items-center gap-2 rounded-md border border-[#dcded8] px-3 py-2 text-sm font-semibold"
              onClick={() => void handleIgnore()}
              type="button"
            >
              <EyeOff aria-hidden="true" size={16} />
              Ignore
            </button>
            <button
              aria-label="Verify chunk"
              className="inline-flex items-center gap-2 rounded-md border border-[#dcded8] px-3 py-2 text-sm font-semibold"
              onClick={() => void handleVerify()}
              type="button"
            >
              <Check aria-hidden="true" size={16} />
              Verify
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
