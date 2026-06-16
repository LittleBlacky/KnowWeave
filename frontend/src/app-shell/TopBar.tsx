"use client";

import { Bot } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

import { generateExpertAgent } from "@/shared/api/knowweave";
import { routeLabelForPath } from "@/shared/config/routes";
import { CommandMenu } from "./CommandMenu";

export function TopBar() {
  const router = useRouter();
  const pathname = usePathname();
  const pageTitle = routeLabelForPath(pathname);
  const [agentBusy, setAgentBusy] = useState(false);

  async function handleGenerateAgent() {
    setAgentBusy(true);
    try {
      await generateExpertAgent("知识库专家");
      router.push("/chat");
    } finally {
      setAgentBusy(false);
    }
  }

  return (
    <header className="mb-6 flex items-start justify-between gap-4 max-md:block">
      <div>
        <nav className="text-xs font-medium text-[#6f756f]">
          KnowWeave
          {pageTitle !== "仪表盘" && ` / ${pageTitle}`}
        </nav>
        <h1 className="mt-1 text-2xl font-semibold tracking-normal text-[#161616]">
          {pageTitle}
        </h1>
      </div>
      <div className="flex items-center gap-3 max-md:mt-4">
        <button
          className="inline-flex items-center gap-2 rounded-lg bg-[#275a53] px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-[#1d433e] disabled:opacity-60"
          disabled={agentBusy}
          onClick={() => void handleGenerateAgent()}
          type="button"
        >
          <Bot aria-hidden="true" size={16} />
          {agentBusy ? "生成中…" : "一键生成专家 Agent"}
        </button>
        <CommandMenu />
      </div>
    </header>
  );
}
