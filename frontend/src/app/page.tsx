"use client";

import {BookOpenCheck, Boxes, FileText, Gauge} from "lucide-react";
import Link from "next/link";
import {useEffect, useState} from "react";

import {AppShell} from "@/app-shell/AppShell";
import {listFiles, listWikiPages} from "@/shared/api/knowweave";
import type {KnowledgeFile, Wiki} from "@/shared/api/knowweave";
import {StatCard, StatCardSkeleton, EmptyState} from "@/shared/ui";

export default function Home() {
  const [files, setFiles] = useState<KnowledgeFile[]>([]);
  const [wikiPages, setWikiPages] = useState<Wiki[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const [fileRes, wikiRes] = await Promise.all([
          listFiles(),
          listWikiPages(),
        ]);
        setFiles(fileRes.items);
        setWikiPages(wikiRes.items);
      } catch {
        // Dashboard is best-effort
      } finally {
        setLoading(false);
      }
    }
    void fetchStats();
  }, []);

  const fileCount = files.length;
  const parsedCount = files.filter((f) => f.status === "parse_succeeded").length;
  const parseRate = fileCount > 0 ? Math.round((parsedCount / fileCount) * 100) : 0;
  const parseFailures = files.filter((f) => f.status === "parse_failed").length;
  const wikiPending = wikiPages.filter(
    (w) => w.status === "draft" || w.status === "pending_review",
  ).length;

  return (
    <AppShell>
      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4 max-2xl:grid-cols-2 max-sm:grid-cols-1">
        {loading ? (
          <>
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
          </>
        ) : (
          <>
            <StatCard
              label="知识文件"
              value={String(fileCount)}
              detail={fileCount === 0 ? "等待上传" : `${parsedCount} 已解析`}
              icon={FileText}
            />
            <StatCard
              label="解析成功率"
              value={`${parseRate}%`}
              detail={parseRate === 0 ? "暂无数据" : `${parsedCount} / ${fileCount} 个文件`}
              icon={Gauge}
              tone={parseRate < 50 && fileCount > 0 ? "warning" : "neutral"}
            />
            <StatCard
              label="知识分块"
              value="—"
              detail="前往分块页面查看"
              icon={Boxes}
            />
            <StatCard
              label="Wiki 页面"
              value={String(wikiPages.length)}
              detail={wikiPages.length === 0 ? "暂无草稿" : `${wikiPending} 待审核`}
              icon={BookOpenCheck}
              tone={wikiPending > 0 ? "warning" : "neutral"}
            />
          </>
        )}
      </div>

      {/* Two-column content */}
      <div className="mt-6 grid grid-cols-[minmax(0,1.3fr)_minmax(300px,0.7fr)] gap-4 max-xl:grid-cols-1">
        {/* Recent files */}
        <section className="rounded-lg border border-[#dcded8] bg-white">
          <div className="border-b border-[#dcded8] px-5 py-3">
            <h2 className="text-base font-semibold">最近添加</h2>
          </div>
          {files.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="暂无文件"
              description="上传知识文件以填充知识库。"
            />
          ) : (
            <div className="divide-y divide-[#dcded8]">
              {files.slice(0, 5).map((file) => (
                <Link
                  key={file.id}
                  href={`/files/${file.id}`}
                  className="flex items-center gap-3 px-5 py-3.5 transition hover:bg-[#f0f2ed]"
                >
                  <FileText aria-hidden="true" className="text-[#275a53]" size={16} />
                  <span className="min-w-0 flex-1 truncate text-sm font-medium">
                    {file.name}
                  </span>
                  <span className="shrink-0 rounded border border-[#dcded8] px-2 py-0.5 text-xs text-[#6f756f]">
                    {file.status}
                  </span>
                </Link>
              ))}
              {files.length > 5 && (
                <div className="px-5 py-3 text-center">
                  <Link href="/files" className="text-sm font-medium text-[#275a53] hover:underline">
                    查看全部 {files.length} 个文件
                  </Link>
                </div>
              )}
            </div>
          )}
        </section>

        {/* Todo queue */}
        <section className="rounded-lg border border-[#dcded8] bg-white">
          <div className="border-b border-[#dcded8] px-5 py-3">
            <h2 className="text-base font-semibold">待处理</h2>
          </div>
          <div className="divide-y divide-[#dcded8]">
            <div className="flex items-center justify-between px-5 py-3.5">
              <span className="text-sm text-[#30342f]">解析失败</span>
              <span
                className={`rounded border px-2 py-0.5 text-xs font-semibold ${
                  parseFailures > 0
                    ? "border-[#e8c8c5] bg-[#fdf4f3] text-[#a23b35]"
                    : "border-[#dcded8] text-[#6f756f]"
                }`}
              >
                {parseFailures}
              </span>
            </div>
            <div className="flex items-center justify-between px-5 py-3.5">
              <span className="text-sm text-[#30342f]">Wiki 待审核</span>
              <span
                className={`rounded border px-2 py-0.5 text-xs font-semibold ${
                  wikiPending > 0
                    ? "border-[#e6d5b3] bg-[#fef9ef] text-[#9a5a13]"
                    : "border-[#dcded8] text-[#6f756f]"
                }`}
              >
                {wikiPending}
              </span>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}

