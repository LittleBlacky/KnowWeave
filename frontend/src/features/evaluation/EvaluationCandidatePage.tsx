"use client";

import { FlaskConical } from "lucide-react";
import { useEffect, useState } from "react";

import { listEvaluationSamples, type EvaluationSample } from "@/shared/api/knowweave";

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
    <section className="rounded-md border border-[#dcded8] bg-white">
      <div className="flex items-center justify-between border-b border-[#dcded8] px-4 py-3">
        <h1 className="text-lg font-semibold">Evaluation Candidates</h1>
        <FlaskConical aria-hidden="true" className="text-[#275a53]" size={20} />
      </div>
      <div className="grid gap-3 p-4">
        {samples.map((sample) => (
          <article className="grid gap-3 rounded-md border border-[#dcded8] p-4" key={sample.id}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="font-semibold">{sample.question}</h2>
              <span className="rounded-md border border-[#dcded8] px-2 py-1 text-xs">
                {sample.status}
              </span>
            </div>
            {sample.expected_answer ? (
              <p className="text-sm text-[#30342f]">{sample.expected_answer}</p>
            ) : null}
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="rounded-md bg-[#e1ebe7] px-2 py-1 font-semibold text-[#123d37]">
                {sample.created_from}
              </span>
              {sample.difficulty ? (
                <span className="rounded-md border border-[#dcded8] px-2 py-1">
                  {sample.difficulty}
                </span>
              ) : null}
              {sample.expected_source_chunks.map((chunkId) => (
                <span className="rounded-md border border-[#dcded8] px-2 py-1" key={chunkId}>
                  {chunkId}
                </span>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
