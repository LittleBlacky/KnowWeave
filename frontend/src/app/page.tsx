import {
  BookOpenCheck,
  Boxes,
  FileText,
  Gauge,
} from "lucide-react";

import { AppShell } from "@/app-shell/AppShell";

const metrics = [
  { label: "Files", value: "0", detail: "ready for upload", icon: FileText },
  { label: "Parse Success", value: "0%", detail: "no runs yet", icon: Gauge },
  { label: "Chunks", value: "0", detail: "awaiting evidence", icon: Boxes },
  { label: "Wiki Pages", value: "0", detail: "draft queue empty", icon: BookOpenCheck },
];

const queueItems = [
  { label: "Parse failures", value: "0", tone: "neutral" },
  { label: "Low quality chunks", value: "0", tone: "warning" },
  { label: "Wiki pending review", value: "0", tone: "neutral" },
  { label: "Citation feedback", value: "0", tone: "danger" },
];

export default function Home() {
  return (
    <AppShell>
      <div className="grid grid-cols-4 gap-4 max-2xl:grid-cols-2 max-sm:grid-cols-1">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <article className="rounded-md border border-[#dcded8] bg-white p-4" key={metric.label}>
              <div className="mb-4 flex items-center justify-between">
                <span className="text-sm text-[#6f756f]">{metric.label}</span>
                <Icon aria-hidden="true" className="text-[#275a53]" size={18} />
              </div>
              <div className="text-3xl font-semibold">{metric.value}</div>
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
          <div className="grid min-h-72 place-items-center px-4 py-10 text-center">
            <div>
              <FileText aria-hidden="true" className="mx-auto mb-3 text-[#275a53]" size={28} />
              <p className="text-sm font-medium">No files indexed</p>
              <p className="mt-1 max-w-md text-sm text-[#6f756f]">
                Upload, parse, and chunk status will appear here once US1 endpoints are wired.
              </p>
            </div>
          </div>
        </section>

        <section className="rounded-md border border-[#dcded8] bg-white">
          <div className="border-b border-[#dcded8] px-4 py-3">
            <h2 className="text-base font-semibold">Action Queue</h2>
          </div>
          <div className="divide-y divide-[#dcded8]">
            {queueItems.map((item) => (
              <div className="flex items-center justify-between px-4 py-3" key={item.label}>
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
