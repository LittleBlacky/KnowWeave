"use client";

import { FlaskConical, Send } from "lucide-react";
import { useState } from "react";

import {
  createEvaluationSampleFromFeedback,
  createFeedback,
  type EvaluationSample,
  type Feedback,
} from "@/shared/api/knowweave";

type FeedbackDialogProps = {
  targetType: string;
  targetId: string;
};

const feedbackTypes = [
  "answer_helpful",
  "answer_wrong",
  "citation_helpful",
  "citation_wrong",
  "retrieval_helpful",
  "retrieval_irrelevant",
  "retrieval_missing",
  "chunk_low_quality",
  "wiki_needs_update",
];

export function FeedbackDialog({ targetId, targetType }: FeedbackDialogProps) {
  const [feedbackType, setFeedbackType] = useState("wiki_needs_update");
  const [comment, setComment] = useState("");
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [sample, setSample] = useState<EvaluationSample | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit() {
    setBusy(true);
    try {
      const created = await createFeedback({
        target_type: targetType,
        target_id: targetId,
        feedback_type: feedbackType,
        comment: comment.trim() || undefined,
        metadata: { source: "frontend" },
      });
      setFeedback(created);
      setSample(null);
    } finally {
      setBusy(false);
    }
  }

  async function handleCreateEvaluationCandidate() {
    if (!feedback) {
      return;
    }
    setBusy(true);
    try {
      setSample(await createEvaluationSampleFromFeedback(feedback.id));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="rounded-md border border-[#dcded8] bg-white">
      <div className="border-b border-[#dcded8] px-4 py-3">
        <h2 className="text-base font-semibold">Feedback</h2>
      </div>
      <div className="grid gap-4 p-4">
        <div className="grid gap-2 rounded-md border border-[#dcded8] bg-[#f7f7f5] p-3 text-sm">
          <div>
            <span className="font-semibold">Target</span> {targetType}
          </div>
          <div className="font-mono text-xs text-[#5d645d]">{targetId}</div>
        </div>
        <label className="grid gap-2 text-sm font-semibold">
          Feedback type
          <select
            className="rounded-md border border-[#dcded8] px-3 py-2 font-normal"
            onChange={(event) => setFeedbackType(event.target.value)}
            value={feedbackType}
          >
            {feedbackTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-2 text-sm font-semibold">
          Feedback comment
          <textarea
            className="min-h-24 resize-y rounded-md border border-[#dcded8] p-3 font-normal"
            onChange={(event) => setComment(event.target.value)}
            value={comment}
          />
        </label>
        <div className="flex flex-wrap gap-2">
          <button
            className="inline-flex items-center gap-2 rounded-md bg-[#123d37] px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
            disabled={busy}
            onClick={() => void handleSubmit()}
            type="button"
          >
            <Send aria-hidden="true" size={16} />
            Submit feedback
          </button>
          <button
            className="inline-flex items-center gap-2 rounded-md border border-[#dcded8] px-3 py-2 text-sm font-semibold disabled:opacity-60"
            disabled={!feedback || busy}
            onClick={() => void handleCreateEvaluationCandidate()}
            type="button"
          >
            <FlaskConical aria-hidden="true" size={16} />
            Create evaluation candidate
          </button>
        </div>
        {feedback ? (
          <div className="rounded-md border border-[#dcded8] p-3 text-sm">
            <div className="font-semibold">{feedback.id}</div>
            <div className="text-[#5d645d]">{feedback.feedback_type}</div>
          </div>
        ) : null}
        {sample ? (
          <div className="rounded-md border border-[#dcded8] bg-[#f0f6f3] p-3 text-sm">
            <div className="font-semibold">{sample.id}</div>
            <div className="text-[#5d645d]">{sample.status}</div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
