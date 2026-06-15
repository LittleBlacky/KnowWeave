"use client";

import { Bot } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { generateExpertAgent } from "@/shared/api/knowweave";
import { CommandMenu } from "./CommandMenu";
import { RouteBreadcrumbs } from "./RouteBreadcrumbs";

export function TopBar() {
  const router = useRouter();
  const [agentBusy, setAgentBusy] = useState(false);

  async function handleGenerateAgent() {
    setAgentBusy(true);
    try {
      const result = await generateExpertAgent("知识库专家");
      router.push("/chat");
    } finally {
      setAgentBusy(false);
    }
  }

  return (
    <header className="mb-6 flex items-start justify-between gap-4 max-md:block">
      <div>
        <RouteBreadcrumbs />
        <h1 className="mt-2 text-2xl font-semibold tracking-normal text-[#161616]">
          知识治理概览
        </h1>
      </div>
      <div className="flex items-center gap-3 max-md:mt-4">
        <button
          className="inline-flex items-center gap-2 rounded-md bg-[#275a53] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60 hover:bg-[#1d433e]"
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
