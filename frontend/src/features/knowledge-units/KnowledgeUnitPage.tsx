"use client";

import {Brain, Check, Network, Sparkles, Trash2, X} from "lucide-react";
import {useCallback, useEffect, useMemo, useState} from "react";

import {
  autoGenerateKnowledgeUnits,
  batchUpdateKnowledgeUnitStatus,
  getKnowledgeUnit,
  listFiles,
  listKnowledgeUnits,
  updateKnowledgeUnit,
  type ExtractionResponse,
  type KnowledgeFile,
  type KnowledgeUnit,
  type KnowledgeUnitDetail,
} from "@/shared/api/knowweave";
import {
  ListPanel,
  DetailPanel,
  ListItemCard,
  Badge,
  EmptyState,
  LoadingState,
} from "@/shared/ui";

const STATUS_OPTIONS = [
  {value: "", label: "全部"},
  {value: "draft", label: "草稿"},
  {value: "verified", label: "已确认"},
  {value: "archived", label: "已归档"},
  {value: "needs_review", label: "待审核"},
];

export function KnowledgeUnitPage() {
  // ---- state ----
  const [units, setUnits] = useState<KnowledgeUnit[]>([]);
  const [detail, setDetail] = useState<KnowledgeUnitDetail | null>(null);
  const [files, setFiles] = useState<KnowledgeFile[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [extracting, setExtracting] = useState<string | null>(null); // fileId being extracted
  const [extractResult, setExtractResult] = useState<ExtractionResponse | null>(
    null,
  );
  const [loading, setLoading] = useState(true);

  // ---- data loading ----
  const loadUnits = useCallback(async () => {
    const params: Record<string, string> = {};
    if (statusFilter) params.status = statusFilter;
    const response = await listKnowledgeUnits(params);
    setUnits(response.items);
  }, [statusFilter]);

  useEffect(() => {
    async function init() {
      setLoading(true);
      await Promise.all([
        loadUnits(),
        listFiles().then((r) => setFiles(r.items)),
      ]);
      setLoading(false);
    }
    void init();
  }, [loadUnits]);

  // ---- selection helpers ----
  const parsedFiles = useMemo(
    () => files.filter((f) => f.status === "parse_succeeded"),
    [files],
  );

  const toggleSelect = (unitId: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(unitId) ? next.delete(unitId) : next.add(unitId);
      return next;
    });
  };

  const clearSelection = () => setSelected(new Set());

  // ---- actions ----
  async function handleSelect(unitId: string) {
    setDetail(await getKnowledgeUnit(unitId));
  }

  async function handleVerifyOne() {
    if (!detail) return;
    setBusy(true);
    try {
      const sourceChunkIds = detail.sources
        .map((s) => s.chunk_id)
        .filter((id): id is string => Boolean(id));
      const verified = await updateKnowledgeUnit(detail.id, {
        title: detail.title,
        unit_type: detail.unit_type,
        content: detail.content,
        summary: detail.summary,
        status: "verified",
        applicable_scope: detail.applicable_scope,
        tag_ids: detail.tags.map((t) => t.id),
        source_chunk_ids: sourceChunkIds,
      });
      setUnits((c) => c.map((u) => (u.id === verified.id ? verified : u)));
      setDetail((c) => (c ? {...c, ...verified} : null));
    } finally {
      setBusy(false);
    }
  }

  async function handleBatchVerify() {
    if (selected.size === 0) return;
    setBusy(true);
    try {
      await batchUpdateKnowledgeUnitStatus([...selected], "verified");
      clearSelection();
      await loadUnits();
      if (detail && selected.has(detail.id)) {
        setDetail(await getKnowledgeUnit(detail.id));
      }
    } finally {
      setBusy(false);
    }
  }

  async function handleBatchArchive() {
    if (selected.size === 0) return;
    setBusy(true);
    try {
      await batchUpdateKnowledgeUnitStatus([...selected], "archived");
      clearSelection();
      await loadUnits();
    } finally {
      setBusy(false);
    }
  }

  async function handleExtract(fileId: string) {
    setExtracting(fileId);
    setExtractResult(null);
    try {
      const result = await autoGenerateKnowledgeUnits(fileId);
      setExtractResult(result);
      await loadUnits();
    } finally {
      setExtracting(null);
    }
  }

  // ---- render ----
  return (
    <div className="grid gap-4">
      {/* Extraction area */}
      <section className="rounded-lg border border-[#dcded8] bg-white p-4">
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="flex items-center gap-2 text-sm font-semibold">
            <Sparkles aria-hidden="true" size={16} className="text-[#275a53]" />
            AI 提取知识
          </h2>
          {parsedFiles.length === 0 ? (
            <p className="text-sm text-[#b0b6ad]">
              暂无已解析的文件，请先上传并解析文件
            </p>
          ) : (
            <div className="flex flex-wrap items-center gap-2">
              {parsedFiles.slice(0, 6).map((file) => (
                <button
                  key={file.id}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-[#dcded8] px-3 py-1.5 text-sm transition hover:border-[#275a53] hover:bg-[#f0f6f3] disabled:opacity-50"
                  disabled={extracting !== null}
                  onClick={() => void handleExtract(file.id)}
                  type="button"
                >
                  <Brain aria-hidden="true" size={14} />
                  {file.name}
                  {extracting === file.id && <LoadingState />}
                </button>
              ))}
            </div>
          )}
        </div>
        {extractResult && (
          <div className="mt-3 flex items-center gap-4 rounded-md bg-[#f0f6f3] px-4 py-2 text-sm">
            <span className="font-semibold text-[#123d37]">
              提取完成：{extractResult.extracted} 个新知识点
            </span>
            {extractResult.skipped_duplicates > 0 && (
              <span className="text-[#6f756f]">
                跳过 {extractResult.skipped_duplicates} 个重复
              </span>
            )}
            <button
              className="ml-auto text-[#6f756f] underline"
              onClick={() => setExtractResult(null)}
              type="button"
            >
              关闭
            </button>
          </div>
        )}
      </section>

      {/* Batch toolbar */}
      {selected.size > 0 && (
        <section className="flex items-center gap-3 rounded-lg border border-[#275a53] bg-[#f0f6f3] px-4 py-2.5">
          <span className="text-sm font-semibold text-[#123d37]">
            已选 {selected.size} 项
          </span>
          <button
            className="inline-flex items-center gap-1.5 rounded-md bg-[#123d37] px-3 py-1.5 text-sm font-semibold text-white transition hover:bg-[#0e2f2a] disabled:opacity-50"
            disabled={busy}
            onClick={() => void handleBatchVerify()}
            type="button"
          >
            <Check aria-hidden="true" size={14} />
            批量确认
          </button>
          <button
            className="inline-flex items-center gap-1.5 rounded-md border border-[#dcded8] bg-white px-3 py-1.5 text-sm text-[#6f756f] transition hover:text-[#a23b35] disabled:opacity-50"
            disabled={busy}
            onClick={() => void handleBatchArchive()}
            type="button"
          >
            <Trash2 aria-hidden="true" size={14} />
            批量归档
          </button>
          <button
            className="ml-auto text-sm text-[#6f756f] underline"
            onClick={clearSelection}
            type="button"
          >
            取消选择
          </button>
        </section>
      )}

      {/* Main list + detail */}
      <div className="grid gap-4 lg:grid-cols-[minmax(320px,0.42fr)_minmax(0,0.58fr)]">
        <ListPanel title="知识单元" icon={Network} count={units.length}>
          {/* Status filter */}
          <div className="mb-2 flex flex-wrap gap-1.5">
            {STATUS_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                className={`rounded-full px-2.5 py-1 text-xs font-medium transition ${
                  statusFilter === opt.value
                    ? "bg-[#123d37] text-white"
                    : "bg-[#f0f2ed] text-[#6f756f] hover:bg-[#dcded8]"
                }`}
                onClick={() => setStatusFilter(opt.value)}
                type="button"
              >
                {opt.label}
              </button>
            ))}
          </div>

          {loading ? (
            <LoadingState />
          ) : units.length === 0 ? (
            <EmptyState
              icon={Network}
              title="暂无知识单元"
              description="上传文件并点击上方的 AI 提取按钮。"
            />
          ) : (
            <div className="grid gap-2">
              {units.map((unit) => (
                <ListItemCard
                  key={unit.id}
                  active={detail?.id === unit.id}
                  onClick={() => {
                    if (selected.size > 0) {
                      toggleSelect(unit.id);
                    } else {
                      void handleSelect(unit.id);
                    }
                  }}
                  title={unit.title}
                  subtitle={unit.summary ?? unit.content}
                  status={unit.status}
                  tags={unit.tags}
                />
              ))}
            </div>
          )}
        </ListPanel>

        <DetailPanel title="单元详情">
          {!detail ? (
            <EmptyState
              icon={Network}
              title="选择知识单元"
              description="从左侧列表选择一个知识单元查看详情。"
            />
          ) : (
            <div className="grid gap-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge>{detail.unit_type}</Badge>
                <Badge
                  tone={detail.status === "verified" ? "accent" : "neutral"}
                >
                  {detail.status}
                </Badge>
                <Badge tone="neutral">{detail.created_from}</Badge>
              </div>

              <div>
                <div className="mb-1 text-sm font-semibold text-[#6f756f]">
                  摘要
                </div>
                <p className="text-sm leading-relaxed">{detail.summary}</p>
              </div>

              <div>
                <div className="mb-1 text-sm font-semibold text-[#6f756f]">
                  内容
                </div>
                <pre className="whitespace-pre-wrap rounded-lg border border-[#dcded8] bg-[#f7f7f5] p-3 text-sm leading-relaxed">
                  {detail.content}
                </pre>
              </div>

              {detail.applicable_scope && (
                <div>
                  <div className="mb-1 text-sm font-semibold text-[#6f756f]">
                    适用范围
                  </div>
                  <p className="text-sm">{detail.applicable_scope}</p>
                </div>
              )}

              {detail.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {detail.tags.map((tag) => (
                    <Badge key={tag.id} tone="accent">
                      {tag.name}
                    </Badge>
                  ))}
                </div>
              )}

              {detail.sources.length > 0 && (
                <div className="grid gap-2">
                  <h3 className="text-sm font-semibold text-[#6f756f]">
                    来源 ({detail.sources.length})
                  </h3>
                  {detail.sources.map((source) => (
                    <div
                      key={source.id}
                      className="rounded-lg border border-[#dcded8] bg-[#f7f7f5] p-3"
                    >
                      <span className="text-sm font-semibold">
                        {source.source_label}
                      </span>
                      <p className="mt-1 text-xs text-[#6f756f]">
                        {source.source_type} ·{" "}
                        {source.source_available ? "可用" : "不可用"}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              <div className="flex gap-2">
                {detail.status !== "verified" && (
                  <button
                    className="inline-flex items-center gap-2 rounded-lg bg-[#123d37] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#0e2f2a] disabled:opacity-50"
                    disabled={busy}
                    onClick={() => void handleVerifyOne()}
                    type="button"
                  >
                    <Check aria-hidden="true" size={16} />
                    确认
                  </button>
                )}
                {detail.status !== "archived" && (
                  <button
                    className="inline-flex items-center gap-2 rounded-lg border border-[#dcded8] bg-white px-4 py-2 text-sm text-[#6f756f] transition hover:border-[#a23b35] hover:text-[#a23b35] disabled:opacity-50"
                    disabled={busy}
                    onClick={async () => {
                      setBusy(true);
                      try {
                        await batchUpdateKnowledgeUnitStatus(
                          [detail.id],
                          "archived",
                        );
                        await loadUnits();
                      } finally {
                        setBusy(false);
                      }
                    }}
                    type="button"
                  >
                    <X aria-hidden="true" size={16} />
                    归档
                  </button>
                )}
              </div>
            </div>
          )}
        </DetailPanel>
      </div>
    </div>
  );
}
