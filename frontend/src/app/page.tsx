"use client";

import {BookOpenCheck, Boxes, FileText, Gauge, Loader2} from "lucide-react";
import Link from "next/link";
import {useEffect, useState} from "react";

import {AppShell} from "@/app-shell/AppShell";
import {listFiles, listWikiPages} from "@/shared/api/knowweave";
import type {KnowledgeFile, Wiki} from "@/shared/api/knowweave";

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
        // Dashboard is best-effort; keep placeholders on error.
      } finally {
        setLoading(false);
      }
    }
    void fetchStats();
  }, []);

  const fileCount = files.length;
  const parsedCount = files.filter(
    (f) => f.status === "parse_succeeded",
  ).length;
  const parseRate =
    fileCount > 0 ? Math.round((parsedCount / fileCount) * 100) : 0;
  const parseFailures = files.filter((f) => f.status === "parse_failed").length;
  const wikiPending = wikiPages.filter(
    (w) => w.status === "draft" || w.status === "pending_review",
  ).length;

  const metrics = [
    {
      label: "Files",
      value: loading ? "…" : String(fileCount),
      detail: fileCount === 0 ? "ready for upload" : `${parsedCount} parsed`,
      icon: FileText,
    },
    {
      label: "Parse Success",
      value: loading ? "…" : `${parseRate}%`,
      detail:
        parseRate === 0
          ? "no runs yet"
          : `${parsedCount} of ${fileCount} files`,
      icon: Gauge,
    },
    {
      label: "Chunks",
      value: loading ? "…" : "—",
      detail: "see Chunks page",
      icon: Boxes,
    },
    {
      label: "Wiki Pages",
      value: loading ? "…" : String(wikiPages.length),
      detail:
        wikiPages.length === 0
          ? "draft queue empty"
          : `${wikiPending} pending review`,
      icon: BookOpenCheck,
    },
  ];

  const queueItems = [
    {
      label: "Parse failures",
      value: String(parseFailures),
      tone: parseFailures > 0 ? "danger" : ("neutral" as const),
    },
    {
      label: "Wiki pending review",
      value: String(wikiPending),
      tone: wikiPending > 0 ? "warning" : ("neutral" as const),
    },
  ];

  return (
    <AppShell>
      <div className="grid grid-cols-4 gap-4 max-2xl:grid-cols-2 max-sm:grid-cols-1">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <article
              className="rounded-md border border-[#dcded8] bg-white p-4"
              key={metric.label}
            >
              <div className="mb-4 flex items-center justify-between">
                <span className="text-sm text-[#6f756f]">{metric.label}</span>
                <Icon aria-hidden="true" className="text-[#275a53]" size={18} />
              </div>
              <div className="flex items-center gap-2 text-3xl font-semibold">
                {loading && (
                  <Loader2
                    aria-hidden="true"
                    className="animate-spin"
                    size={24}
                  />
                )}
                {metric.value}
              </div>
              <div className="mt-1 text-sm text-[#6f756f]">{metric.detail}</div>
            </article>
          );
        })}
      </div>

      <div className="mt-6 grid grid-cols-[minmax(0,1.3fr)_minmax(300px,0.7fr)] gap-4 max-xl:grid-cols-1">
        <section className="rounded-md border border-[#dcded8] bg-white">
          <div className="border-b border-[#dcded8] px-4 py-3">
            <h2 className="text-base font-semibold">Recent Evidence</h2>
          </div>
          {files.length === 0 ? (
            <div className="grid min-h-72 place-items-center px-4 py-10 text-center">
              <div>
                <FileText
                  aria-hidden="true"
                  className="mx-auto mb-3 text-[#275a53]"
                  size={28}
                />
                <p className="text-sm font-medium">No files indexed</p>
                <p className="mt-1 max-w-md text-sm text-[#6f756f]">
                  Upload evidence files to populate the knowledge base.
                </p>
              </div>
            </div>
          ) : (
            <div className="divide-y divide-[#dcded8]">
              {files.slice(0, 5).map((file) => (
                <Link
                  key={file.id}
                  href={`/files/${file.id}`}
                  className="flex items-center gap-3 px-4 py-3 hover:bg-[#f0f2ed]"
                >
                  <FileText
                    aria-hidden="true"
                    className="text-[#275a53]"
                    size={16}
                  />
                  <span className="flex-1 truncate text-sm font-medium">
                    {file.name}
                  </span>
                  <span className="rounded-md border border-[#dcded8] px-2 py-1 text-xs text-[#6f756f]">
                    {file.status}
                  </span>
                </Link>
              ))}
              {files.length > 5 && (
                <div className="px-4 py-3 text-center">
                  <Link
                    href="/files"
                    className="text-sm text-[#275a53] hover:underline"
                  >
                    View all {files.length} files
                  </Link>
                </div>
              )}
            </div>
          )}
        </section>

        <section className="rounded-md border border-[#dcded8] bg-white">
          <div className="border-b border-[#dcded8] px-4 py-3">
            <h2 className="text-base font-semibold">Action Queue</h2>
          </div>
          <div className="divide-y divide-[#dcded8]">
            {queueItems.map((item) => (
              <div
                className="flex items-center justify-between px-4 py-3"
                key={item.label}
              >
                <span className="text-sm text-[#30342f]">{item.label}</span>
                <span
                  className="rounded-md border border-[#dcded8] px-2 py-1 text-xs font-semibold"
                  data-tone={item.tone}
                >
                  {item.value}
                </span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  );
}

