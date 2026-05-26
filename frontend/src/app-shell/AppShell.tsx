import { BotMessageSquare, MessageSquareWarning } from "lucide-react";
import type { ReactNode } from "react";

import { AppSidebar } from "./AppSidebar";
import { TopBar } from "./TopBar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <main className="min-h-screen bg-[#f7f7f5] text-[#161616]">
      <div className="grid min-h-screen grid-cols-[240px_minmax(0,1fr)_320px] max-xl:grid-cols-[220px_minmax(0,1fr)] max-lg:grid-cols-1">
        <AppSidebar />

        <section className="px-8 py-6 max-sm:px-4">
          <TopBar />
          {children}
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
