"use client";

import { FlaskConical } from "lucide-react";
import { useEffect, useState } from "react";

import { listEvaluationSamples, type EvaluationSample } from "@/shared/api/knowweave";
import { ListPanel, Badge, EmptyState } from "@/shared/ui";

export function EvaluationCandidatePage() {
  const [samples, setSamples] = useState<EvaluationSample[]>([]);

  useEffect(() => {
    async function loadSamples() {
      const response = await listEvaluationSamples();
      setSamples(response.items);
    }
    void loadSamples();
  }, []);

  return (
    <div className="grid gap-4">
      <ListPanel title="评测候选" icon={FlaskConical} count={samples.length}>
        {samples.length === 0 ? (
          <EmptyState
            icon={FlaskConical}
            title="暂无评测候选"
            description="知识库中尚未生成评测样本。"
          />
        ) : (
          <div className="grid gap-3">
            {samples.map((sample) => (
              <article
                key={sample.id}
                className="rounded-lg border border-[#dcded8] p-4"
              >
                <div className="mb-2 flex flex-wrap items-start justify-between gap-2">
                  <h2 className="text-sm font-semibold">{sample.question}</h2>
                  <Badge tone={sample.status === "verified" ? "accent" : "neutral"}>
                    {sample.status}
                  </Badge>
                </div>
                {sample.expected_answer && (
                  <p className="text-sm leading-relaxed text-[#30342f]">
                    {sample.expected_answer}
                  </p>
                )}
                <div className="mt-3 flex flex-wrap gap-1.5">
                  <Badge>{sample.created_from}</Badge>
                  {sample.difficulty && (
                    <Badge tone="warning">{sample.difficulty}</Badge>
                  )}
                  {sample.expected_source_chunks.map((chunkId) => (
                    <span
                      key={chunkId}
                      className="rounded bg-[#f0f2ed] px-2 py-0.5 text-xs text-[#6f756f]"
                    >
                      {chunkId}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        )}
      </ListPanel>
    </div>
  );
}
