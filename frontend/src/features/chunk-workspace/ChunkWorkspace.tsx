"use client";

import {Check, EyeOff, Flag, Save} from "lucide-react";
import {useEffect, useMemo, useState} from "react";

import {
  ignoreChunk,
  listFileChunks,
  listFiles,
  updateChunk,
  verifyChunk,
  type Chunk,
} from "@/shared/api/knowweave";
import {FeedbackDialog} from "@/features/feedback/FeedbackDialog";
import {SourceLocatorPanel} from "@/features/source-viewer/SourceLocatorPanel";
import {
  ListPanel,
  DetailPanel,
  ListItemCard,
  Badge,
  EmptyState,
} from "@/shared/ui";

export function ChunkWorkspace() {
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [showFeedback, setShowFeedback] = useState(false);
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
      setDraft(
        response.items[0]?.edited_content ??
          response.items[0]?.raw_content ??
          "",
      );
    }
    void load();
  }, []);

  function replaceChunk(next: Chunk) {
    setChunks((current) =>
      current.map((chunk) => (chunk.id === next.id ? next : chunk)),
    );
    setSelectedId(next.id);
    setDraft(next.edited_content ?? next.raw_content);
  }

  async function handleSave() {
    if (!selected) return;
    replaceChunk(await updateChunk(selected.id, draft));
  }

  async function handleIgnore() {
    if (!selected) return;
    replaceChunk(await ignoreChunk(selected.id));
  }

  async function handleVerify() {
    if (!selected) return;
    replaceChunk(await verifyChunk(selected.id));
  }

  if (chunks.length === 0) {
    return (
      <EmptyState
        title="暂无分块"
        description="上传文件并解析后，分块将在此显示。"
      />
    );
  }

  const source = selected.source_spans[0]
    ? {...selected.source_spans[0], file_id: selected.file_id}
    : undefined;

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(320px,0.42fr)_minmax(0,0.58fr)]">
      <ListPanel title="分块列表" count={chunks.length}>
        <div className="grid gap-2">
          {chunks.map((chunk) => (
            <ListItemCard
              key={chunk.id}
              active={chunk.id === selected.id}
              onClick={() => {
                setSelectedId(chunk.id);
                setDraft(chunk.edited_content ?? chunk.raw_content);
              }}
              title={`Chunk ${chunk.chunk_index + 1}`}
              subtitle={chunk.edited_content ?? chunk.raw_content}
              status={chunk.status}
            />
          ))}
        </div>
      </ListPanel>

      <DetailPanel title="分块详情">
        <div className="grid gap-4">
          <div>
            <div className="mb-2 text-sm font-semibold text-[#6f756f]">
              原始内容
            </div>
            <pre className="whitespace-pre-wrap rounded-lg border border-[#dcded8] bg-[#f7f7f5] p-3 text-sm leading-relaxed">
              {selected.raw_content}
            </pre>
          </div>

          <label className="grid gap-1.5 text-sm font-semibold">
            编辑内容
            <textarea
              className="min-h-32 resize-y rounded-lg border border-[#dcded8] p-3 text-sm font-normal focus:border-[#275a53] focus:outline-none"
              onChange={(e) => setDraft(e.target.value)}
              value={draft}
            />
          </label>

          <SourceLocatorPanel source={source} />

          <div className="flex flex-wrap gap-2">
            <button
              className="inline-flex items-center gap-2 rounded-lg bg-[#123d37] px-3.5 py-2 text-sm font-semibold text-white transition hover:bg-[#0e2f2a]"
              onClick={() => void handleSave()}
              type="button"
            >
              <Save aria-hidden="true" size={16} />
              保存
            </button>
            <button
              className="inline-flex items-center gap-2 rounded-lg border border-[#dcded8] px-3.5 py-2 text-sm font-semibold transition hover:bg-[#f0f2ed]"
              onClick={() => void handleIgnore()}
              type="button"
            >
              <EyeOff aria-hidden="true" size={16} />
              忽略
            </button>
            <button
              className="inline-flex items-center gap-2 rounded-lg border border-[#dcded8] px-3.5 py-2 text-sm font-semibold transition hover:bg-[#f0f2ed]"
              onClick={() => void handleVerify()}
              type="button"
            >
              <Check aria-hidden="true" size={16} />
              验证
            </button>
            <button
              className="inline-flex items-center gap-2 rounded-lg border border-[#dcded8] px-3.5 py-2 text-sm font-semibold text-[#6f756f] transition hover:border-[#a23b35] hover:text-[#a23b35]"
              onClick={() => setShowFeedback((v) => !v)}
              type="button"
            >
              <Flag aria-hidden="true" size={16} />
              反馈
            </button>
          </div>

          {showFeedback && (
            <FeedbackDialog targetId={selected.id} targetType="chunk" />
          )}
        </div>
      </DetailPanel>
    </div>
  );
}
