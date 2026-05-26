import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EvaluationCandidatePage } from "./EvaluationCandidatePage";

describe("EvaluationCandidatePage", () => {
  it("lists evaluation candidates with question, answer, source and status", async () => {
    render(<EvaluationCandidatePage />);

    expect(await screen.findByText("Who approves leave requests?")).toBeInTheDocument();
    expect(screen.getByText("Managers approve leave requests.")).toBeInTheDocument();
    expect(screen.getByText("candidate")).toBeInTheDocument();
    expect(screen.getByText("feedback")).toBeInTheDocument();
    expect(screen.getByText("chunk_policy")).toBeInTheDocument();
  });
});
