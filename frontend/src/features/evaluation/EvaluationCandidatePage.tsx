"use client";

import {Check, FlaskConical, Save, X} from "lucide-react";
import {useCallback, useEffect, useState} from "react";

import {
  getEvaluationMetrics,
  getEvaluationSample,
  listEvaluationSamples,
  updateEvaluationSample,
  type EvaluationMetrics,
  type EvaluationSample,
} from "@/shared/api/knowweave";
import {ListPanel, DetailPanel, Badge, EmptyState} from "@/shared/ui";

const STATUS_TABS = [
  {value: "", label: "全部"},
  {value: "candidate", label: "候选"},
  {value: "verified", label: "已验证"},
  {value: "rejected", label: "已拒绝"},
];

export function EvaluationCandidatePage() {
  const [samples, setSamples] = useState<EvaluationSample[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [selected, setSelected] = useState<EvaluationSample | null>(null);
  const [metrics, setMetrics] = useState<EvaluationMetrics | null>(null);

  // Detail form state
  const [editQuestion, setEditQuestion] = useState("");
  const [editAnswer, setEditAnswer] = useState("");
  const [editDifficulty, setEditDifficulty] = useState("");
  const [busy, setBusy] = useState(false);

  const loadSamples = useCallback(async () => {
    const response = await listEvaluationSamples(statusFilter || undefined);
    setSamples(response.items);
  }, [statusFilter]);

  useEffect(() => {
    void loadSamples();
    void getEvaluationMetrics()
      .then(setMetrics)
      .catch(() => {});
  }, [loadSamples]);

  async function handleSelect(sampleId: string) {
    const detail = await getEvaluationSample(sampleId);
    setSelected(detail);
    setEditQuestion(detail.question);
    setEditAnswer(detail.expected_answer ?? "");
    setEditDifficulty(detail.difficulty ?? "");
  }

  async function handleSave() {
    if (!selected) return;
    setBusy(true);
    try {
      const updated = await updateEvaluationSample(selected.id, {
        question: editQuestion,
        expected_answer: editAnswer || null,
        difficulty: editDifficulty || null,
      });
      setSelected(updated);
      setSamples((c) => c.map((s) => (s.id === updated.id ? updated : s)));
    } finally {
      setBusy(false);
    }
  }

  async function handleSetStatus(status: string) {
    if (!selected) return;
    setBusy(true);
    try {
      const updated = await updateEvaluationSample(selected.id, {status});
      setSelected(updated);
      setSamples((c) => c.map((s) => (s.id === updated.id ? updated : s)));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-4">
      {/* Metrics cards */}
      {metrics && metrics.total_samples > 0 && (
        <div className="grid grid-cols-3 gap-3">
          <MetricCard label="候选总数" value={metrics.total_samples} />
          <MetricCard label="已验证" value={metrics.verified ?? 0} />
          <MetricCard
            label="带答案"
            value={
              metrics.answer_coverage_pct != null
                ? `${metrics.answer_coverage_pct}%`
                : (metrics.with_answer ?? 0)
            }
          />
        </div>
      )}

      {/* Status filter */}
      <div className="flex gap-2">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value}
            className={`rounded-lg px-3 py-1.5 text-sm transition ${
              statusFilter === tab.value
                ? "bg-[#123d37] text-white"
                : "border border-[#dcded8] text-[#6f756f] hover:bg-[#f0f2ed]"
            }`}
            onClick={() => setStatusFilter(tab.value)}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* List + Detail */}
      <div className="grid gap-4 lg:grid-cols-[minmax(320px,0.4fr)_minmax(0,0.6fr)]">
        <ListPanel title="评测候选" icon={FlaskConical} count={samples.length}>
          {samples.length === 0 ? (
            <EmptyState
              icon={FlaskConical}
              title="暂无评测候选"
              description="将反馈或对话转为评测样本。"
            />
          ) : (
            <div className="grid gap-2">
              {samples.map((sample) => (
                <button
                  key={sample.id}
                  className={`grid gap-1.5 rounded-lg border p-3 text-left transition ${
                    selected?.id === sample.id
                      ? "border-[#275a53] bg-[#f0f6f3]"
                      : "border-[#dcded8] hover:border-[#275a53]"
                  }`}
                  onClick={() => void handleSelect(sample.id)}
                  type="button"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-sm font-semibold line-clamp-2">
                      {sample.question}
                    </span>
                    <Badge
                      tone={
                        sample.status === "verified"
                          ? "accent"
                          : sample.status === "rejected"
                            ? "danger"
                            : "neutral"
                      }
                    >
                      {sample.status}
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    <Badge>{sample.created_from}</Badge>
                    {sample.difficulty && (
                      <Badge tone="warning">{sample.difficulty}</Badge>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </ListPanel>

        <DetailPanel title={selected ? undefined : "样本详情"}>
          {!selected ? (
            <EmptyState
              icon={FlaskConical}
              title="选择评测样本"
              description="从左侧列表选择一个样本查看和编辑详情。"
            />
          ) : (
            <div className="grid gap-4">
              {/* Status actions */}
              <div className="flex flex-wrap items-center gap-2">
                <Badge>{selected.created_from}</Badge>
                <Badge
                  tone={
                    selected.status === "verified"
                      ? "accent"
                      : selected.status === "rejected"
                        ? "danger"
                        : "neutral"
                  }
                >
                  {selected.status}
                </Badge>
                {selected.difficulty && (
                  <Badge tone="warning">{selected.difficulty}</Badge>
                )}
                <div className="ml-auto flex gap-1.5">
                  <button
                    className="inline-flex items-center gap-1 rounded border border-[#275a53] px-2.5 py-1 text-xs font-semibold text-[#275a53] hover:bg-[#f0f6f3] disabled:opacity-50"
                    disabled={busy || selected.status === "verified"}
                    onClick={() => void handleSetStatus("verified")}
                    type="button"
                  >
                    <Check size={13} />
                    验证
                  </button>
                  <button
                    className="inline-flex items-center gap-1 rounded border border-[#a23b35] px-2.5 py-1 text-xs font-semibold text-[#a23b35] hover:bg-[#fdf4f3] disabled:opacity-50"
                    disabled={busy || selected.status === "rejected"}
                    onClick={() => void handleSetStatus("rejected")}
                    type="button"
                  >
                    <X size={13} />
                    拒绝
                  </button>
                </div>
              </div>

              {/* Question */}
              <label className="grid gap-1.5 text-sm font-semibold">
                问题
                <textarea
                  className="min-h-[60px] resize-y rounded-lg border border-[#dcded8] p-3 text-sm font-normal focus:border-[#275a53] focus:outline-none"
                  onChange={(e) => setEditQuestion(e.target.value)}
                  value={editQuestion}
                />
              </label>

              {/* Expected answer */}
              <label className="grid gap-1.5 text-sm font-semibold">
                预期答案
                <textarea
                  className="min-h-[100px] resize-y rounded-lg border border-[#dcded8] p-3 text-sm font-normal focus:border-[#275a53] focus:outline-none"
                  onChange={(e) => setEditAnswer(e.target.value)}
                  value={editAnswer}
                />
              </label>

              {/* Difficulty */}
              <label className="grid gap-1.5 text-sm font-semibold">
                难度
                <input
                  className="rounded-lg border border-[#dcded8] px-3 py-2 text-sm font-normal focus:border-[#275a53] focus:outline-none"
                  onChange={(e) => setEditDifficulty(e.target.value)}
                  placeholder="easy / medium / hard"
                  value={editDifficulty}
                />
              </label>

              {/* Source info */}
              {selected.expected_source_chunks.length > 0 && (
                <div>
                  <span className="text-xs font-semibold text-[#6f756f]">
                    关联 Chunks
                  </span>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {selected.expected_source_chunks.map((id) => (
                      <code
                        key={id}
                        className="rounded bg-[#f0f2ed] px-2 py-0.5 text-xs text-[#6f756f]"
                      >
                        {id.slice(0, 8)}
                      </code>
                    ))}
                  </div>
                </div>
              )}

              {/* Save */}
              <button
                className="inline-flex items-center gap-2 self-start rounded-lg bg-[#123d37] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#0e2f2a] disabled:opacity-50"
                disabled={busy}
                onClick={() => void handleSave()}
                type="button"
              >
                <Save size={16} />
                保存修改
              </button>
            </div>
          )}
        </DetailPanel>
      </div>
    </div>
  );
}

function MetricCard({label, value}: {label: string; value: string | number}) {
  return (
    <div className="rounded-lg border border-[#dcded8] bg-white px-4 py-3">
      <span className="text-xs text-[#6f756f]">{label}</span>
      <p className="mt-1 text-2xl font-bold text-[#123d37]">{value}</p>
    </div>
  );
}
