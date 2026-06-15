"use client";

import {
  BarChart3,
  BookOpenCheck,
  FileWarning,
  Lightbulb,
  Loader2,
  MessageSquare,
} from "lucide-react";
import { useEffect, useState } from "react";

import { AppShell } from "@/app-shell/AppShell";
import { getCurationReport, type CurationReport } from "@/shared/api/knowweave";

export default function CurationPage() {
  const [report, setReport] = useState<CurationReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetch() {
      try {
        const data = await getCurationReport();
        setReport(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load report");
      } finally {
        setLoading(false);
      }
    }
    void fetch();
  }, []);

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center py-20">
          <Loader2 aria-hidden="true" className="animate-spin text-[#275a53]" size={32} />
        </div>
      </AppShell>
    );
  }

  if (error || !report) {
    return (
      <AppShell>
        <div className="py-20 text-center text-sm text-[#6f756f]">{error || "No data"}</div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <h1 className="mb-2 text-xl font-semibold">知识策展</h1>
      <p className="mb-6 text-sm text-[#6f756f]">
        LLM 驱动的知识发现报告。生成时间: {new Date(report.generated_at).toLocaleString()}。
      </p>

      {/* Stats cards */}
      <div className="mb-6 grid grid-cols-4 gap-4 max-2xl:grid-cols-2 max-sm:grid-cols-1">
        <StatCard label="知识分块" value={report.total_chunks} icon={BarChart3} />
        <StatCard label="知识单元" value={report.total_knowledge_units} icon={BookOpenCheck} />
        <StatCard label="Wiki 页面" value={report.total_wiki_pages} icon={BookOpenCheck} />
        <StatCard label="反馈信号" value={report.total_feedback_count} icon={MessageSquare} />
      </div>

      {/* Summary */}
      <section className="mb-6 rounded-md border border-[#dcded8] bg-[#e1ebe7] p-4">
        <div className="flex items-center gap-2 mb-2">
          <Lightbulb aria-hidden="true" className="text-[#123d37]" size={18} />
          <h2 className="font-semibold">AI 摘要</h2>
        </div>
        <p className="text-sm whitespace-pre-wrap text-[#123d37]">{report.summary}</p>
      </section>

      <div className="grid grid-cols-2 gap-6 max-xl:grid-cols-1">
        {/* High-value chunks */}
        <section className="rounded-md border border-[#dcded8] bg-white">
          <div className="border-b border-[#dcded8] px-4 py-3">
            <h2 className="font-semibold">
              高价值分块 ({report.high_value_chunks.length})
            </h2>
          </div>
          <div className="divide-y divide-[#dcded8]">
            {report.high_value_chunks.length === 0 ? (
                <p className="px-4 py-6 text-sm text-[#6f756f]">暂无高价值分块。</p>
            ) : (
              report.high_value_chunks.map((chunk) => (
                <div key={chunk.chunk_id} className="px-4 py-3">
                  <p className="text-sm font-medium">{chunk.file_name}</p>
                  <p className="mt-1 text-xs text-[#6f756f] line-clamp-2">{chunk.preview}</p>
                  <span className="mt-1 inline-block rounded bg-[#f0f2ed] px-2 py-0.5 text-xs">
                    {chunk.status}
                  </span>
                </div>
              ))
            )}
          </div>
        </section>

        {/* Suggested topics + frequent questions */}
        <div className="flex flex-col gap-6">
          <section className="rounded-md border border-[#dcded8] bg-white">
            <div className="border-b border-[#dcded8] px-4 py-3">
              <h2 className="font-semibold">
                建议主题 ({report.suggested_topics.length})
              </h2>
            </div>
            <div className="divide-y divide-[#dcded8]">
              {report.suggested_topics.length === 0 ? (
                <p className="px-4 py-6 text-sm text-[#6f756f]">暂无主题建议。</p>
              ) : (
                report.suggested_topics.map((topic, i) => (
                  <div key={i} className="px-4 py-3">
                    <p className="text-sm">{topic}</p>
                  </div>
                ))
              )}
            </div>
          </section>

          <section className="rounded-md border border-[#dcded8] bg-white">
            <div className="border-b border-[#dcded8] px-4 py-3">
              <h2 className="font-semibold">
                高频问题 ({report.frequent_questions.length})
              </h2>
            </div>
            <div className="divide-y divide-[#dcded8]">
              {report.frequent_questions.length === 0 ? (
                <p className="px-4 py-6 text-sm text-[#6f756f]">暂无聊天提问记录。</p>
              ) : (
                report.frequent_questions.map((q, i) => (
                  <div key={i} className="px-4 py-3">
                    <p className="text-sm">{q}</p>
                  </div>
                ))
              )}
            </div>
          </section>

          {/* Stale items */}
          <section className="rounded-md border border-[#dcded8] bg-white">
            <div className="border-b border-[#dcded8] px-4 py-3">
              <h2 className="font-semibold flex items-center gap-2">
                <FileWarning aria-hidden="true" className="text-amber-600" size={16} />
                待审核 ({report.stale_items.length})
              </h2>
            </div>
            <div className="divide-y divide-[#dcded8]">
              {report.stale_items.length === 0 ? (
                <p className="px-4 py-6 text-sm text-[#6f756f]">所有知识均为最新状态。</p>
              ) : (
                report.stale_items.map((item) => (
                  <div key={item.id} className="px-4 py-3">
                    <p className="text-xs text-[#6f756f]">{item.type} · {item.last_updated}</p>
                    <p className="mt-1 text-sm line-clamp-2">{item.preview}</p>
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

function StatCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: number;
  icon: React.ComponentType<{ className?: string; size?: number }>;
}) {
  return (
    <article className="rounded-md border border-[#dcded8] bg-white p-4">
      <div className="mb-4 flex items-center justify-between">
        <span className="text-sm text-[#6f756f]">{label}</span>
        <Icon aria-hidden="true" className="text-[#275a53]" size={18} />
      </div>
      <div className="text-3xl font-semibold">{value}</div>
    </article>
  );
}
