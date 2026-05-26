import {
  BookOpenCheck,
  BotMessageSquare,
  Boxes,
  FileText,
  Gauge,
  MessageSquareWarning,
  Search,
} from "lucide-react";

const navItems = [
  "Dashboard",
  "Files",
  "Chunks",
  "Knowledge Units",
  "Wiki",
  "Search",
  "Chat",
  "Evaluation",
];

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
    <main className="min-h-screen bg-[#f7f7f5] text-[#161616]">
      <div className="grid min-h-screen grid-cols-[240px_minmax(0,1fr)_320px] max-xl:grid-cols-[220px_minmax(0,1fr)] max-lg:grid-cols-1">
        <aside className="border-r border-[#dcded8] bg-[#ffffff] px-5 py-5 max-lg:border-b max-lg:border-r-0">
          <div className="mb-8 flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-md bg-[#123d37] text-sm font-semibold text-white">
              KW
            </div>
            <div>
              <div className="text-sm font-semibold">KnowWeave</div>
              <div className="text-xs text-[#6f756f]">P0 Workbench</div>
            </div>
          </div>
          <nav className="grid gap-1">
            {navItems.map((item) => (
              <a
                className="rounded-md px-3 py-2 text-sm text-[#30342f] transition hover:bg-[#f0f2ed]"
                href="#"
                key={item}
              >
                {item}
              </a>
            ))}
          </nav>
        </aside>

        <section className="px-8 py-6 max-sm:px-4">
          <header className="mb-6 flex items-start justify-between gap-4 max-md:block">
            <div>
              <p className="mb-2 text-xs font-semibold uppercase text-[#275a53]">Dashboard</p>
              <h1 className="text-2xl font-semibold tracking-normal text-[#161616]">
                Evidence Governance Overview
              </h1>
            </div>
            <div className="flex items-center gap-2 rounded-md border border-[#dcded8] bg-white px-3 py-2 text-sm text-[#30342f] max-md:mt-4">
              <Search aria-hidden="true" size={16} />
              <span>Search files, chunks, wiki</span>
            </div>
          </header>

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
        </section>

        <aside className="border-l border-[#dcded8] bg-[#ffffff] px-5 py-6 max-xl:hidden">
          <div className="mb-4 flex items-center gap-2">
            <BotMessageSquare aria-hidden="true" className="text-[#275a53]" size={18} />
            <h2 className="text-base font-semibold">Context</h2>
          </div>
          <div className="rounded-md border border-[#dcded8] bg-[#f0f2ed] p-4">
            <div className="mb-2 flex items-center gap-2 text-sm font-medium">
              <MessageSquareWarning aria-hidden="true" size={16} />
              Retrieved Contexts
            </div>
            <p className="text-sm text-[#5d645d]">
              Source spans, citations, retrieval runs, and quality signals will share this panel.
            </p>
          </div>
        </aside>
      </div>
    </main>
  );
}
