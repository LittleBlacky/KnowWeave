import type {ReactNode} from "react";

import {AppSidebar} from "./AppSidebar";
import {TopBar} from "./TopBar";

export function AppShell({children}: {children: ReactNode}) {
  return (
    <main className="min-h-screen bg-[#f7f7f5] text-[#161616]">
      <div className="grid min-h-screen grid-cols-[240px_minmax(0,1fr)] max-lg:grid-cols-1">
        <AppSidebar />

        <section className="px-8 py-6 max-sm:px-4">
          <TopBar />
          {children}
        </section>
      </div>
    </main>
  );
}

