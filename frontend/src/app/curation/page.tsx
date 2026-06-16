"use client";

import {
  BarChart3, BookOpenCheck, FileWarning, Lightbulb, MessageSquare,
} from "lucide-react";
import { useEffect, useState } from "react";

import { AppShell } from "@/app-shell/AppShell";
import { getCurationReport, type CurationReport } from "@/shared/api/knowweave";
import { StatCard, StatCardSkeleton, Badge, EmptyState, LoadingState, ErrorState } from "@/shared/ui";

export default function CurationPage() {
  const [report, setReport] = useState<CurationReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function fetch() {
    setLoading(true);
    setError("");
    try {
      const data = await getCurationReport();
      setReport(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void fetch(); }, []);

  if (loading) {
    return (
      <AppShell>
        <div className="grid grid-cols-4 gap-4 max-2xl:grid-cols-2 max-sm:grid-cols-1">
          <StatCardSkeleton /><StatCardSkeleton /><StatCardSkeleton /><StatCardSkeleton />
        </div>
      </AppShell>
    );
  }

  if (error || !report) {
    return (
      <AppShell>
        <ErrorState message={error || "暂无数据"} onRetry={() => void fetch()} />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <p className="mb-6 text-sm text-[#6f756f]">
        LLM 驱动的知识发现报告 · 生成时间: {new Date(report.generated_at).toLocaleString()}
      </p>

      {/* Stats */}
      <div className="mb-6 grid grid-cols-4 gap-4 max-2xl:grid-cols-2 max-sm:grid-cols-1">
        <StatCard label="知识分块" value={String(report.total_chunks)} icon={BarChart3} />
        <StatCard label="知识单元" value={String(report.total_knowledge_units)} icon={BookOpenCheck} />
        <StatCard label="Wiki 页面" value={String(report.total_wiki_pages)} icon={BookOpenCheck} />
        <StatCard label="反馈信号" value={String(report.total_feedback_count)} icon={MessageSquare} />
      </div>

      {/* AI Summary */}
      <section className="mb-6 rounded-lg border border-[#b8d4cd] bg-[#e1ebe7] p-5">
        <div className="mb-2 flex items-center gap-2">
          <Lightbulb aria-hidden="true" className="text-[#123d37]" size={18} />
          <h2 className="font-semibold">AI 摘要</h2>
        </div>
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-[#123d37]">
          {report.summary}
        </p>
      </section>

      {/* Detail sections */}
      <div className="grid grid-cols-2 gap-4 max-xl:grid-cols-1">
        {/* High-value chunks */}
        <section className="rounded-lg border border-[#dcded8] bg-white">
          <div className="border-b border-[#dcded8] px-5 py-3">
            <h2 className="font-semibold">高价值分块 ({report.high_value_chunks.length})</h2>
          </div>
          <div className="divide-y divide-[#dcded8]">
            {report.high_value_chunks.length === 0 ? (
              <p className="px-5 py-8 text-center text-sm text-[#6f756f]">暂无高价值分块</p>
            ) : (
              report.high_value_chunks.map((chunk) => (
                <div key={chunk.chunk_id} className="px-5 py-3.5">
                  <p className="text-sm font-medium">{chunk.file_name}</p>
                  <p className="mt-1 line-clamp-2 text-xs text-[#5d645d]">{chunk.preview}</p>
                  <Badge tone="accent">{chunk.status}</Badge>
                </div>
              ))
            )}
          </div>
        </section>

        {/* Right column: Topics + Questions + Stale */}
        <div className="flex flex-col gap-4">
          <section className="rounded-lg border border-[#dcded8] bg-white">
            <div className="border-b border-[#dcded8] px-5 py-3">
              <h2 className="font-semibold">建议主题 ({report.suggested_topics.length})</h2>
            </div>
            <div className="divide-y divide-[#dcded8]">
              {report.suggested_topics.length === 0 ? (
                <p className="px-5 py-8 text-center text-sm text-[#6f756f]">暂无主题建议</p>
              ) : (
                report.suggested_topics.map((topic, i) => (
                  <div key={i} className="px-5 py-3 text-sm">{topic}</div>
                ))
              )}
            </div>
          </section>

          <section className="rounded-lg border border-[#dcded8] bg-white">
            <div className="border-b border-[#dcded8] px-5 py-3">
              <h2 className="font-semibold">高频问题 ({report.frequent_questions.length})</h2>
            </div>
            <div className="divide-y divide-[#dcded8]">
              {report.frequent_questions.length === 0 ? (
                <p className="px-5 py-8 text-center text-sm text-[#6f756f]">暂无聊天提问记录</p>
              ) : (
                report.frequent_questions.map((q, i) => (
                  <div key={i} className="px-5 py-3 text-sm">{q}</div>
                ))
              )}
            </div>
          </section>

          <section className="rounded-lg border border-[#dcded8] bg-white">
            <div className="border-b border-[#dcded8] px-5 py-3">
              <h2 className="flex items-center gap-2 font-semibold">
                <FileWarning aria-hidden="true" className="text-[#9a5a13]" size={16} />
                待审核 ({report.stale_items.length})
              </h2>
            </div>
            <div className="divide-y divide-[#dcded8]">
              {report.stale_items.length === 0 ? (
                <p className="px-5 py-8 text-center text-sm text-[#6f756f]">所有知识均为最新状态</p>
              ) : (
                report.stale_items.map((item) => (
                  <div key={item.id} className="px-5 py-3.5">
                    <div className="mb-1 flex items-center gap-2">
                      <Badge tone="warning">{item.type}</Badge>
                      <span className="text-xs text-[#6f756f]">{item.last_updated}</span>
                    </div>
                    <p className="line-clamp-2 text-sm">{item.preview}</p>
                  </div>
                ))
              )}
            </div>
          </section>
        </div>
      </div>
    </AppShell>
  );
}
