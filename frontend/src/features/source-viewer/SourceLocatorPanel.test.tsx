import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SourceLocatorPanel } from "./SourceLocatorPanel";

describe("SourceLocatorPanel", () => {
  it("shows an enabled source action for available locators", () => {
    render(
      <SourceLocatorPanel
        source={{
          char_end: null,
          char_start: null,
          document_block_id: "block_policy",
          id: "span_policy",
          line_end: 3,
          line_start: 1,
          page_number: null,
          preview_text: "Leave requests need approval.",
          source_available: true,
          source_label: "policy.md",
        }}
      />,
    );

    expect(screen.getByText("policy.md")).toBeInTheDocument();
    expect(screen.getByText("Lines 1-3")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open source" })).toBeEnabled();
  });

  it("keeps citation snapshots visible when source is unavailable", () => {
    render(
      <SourceLocatorPanel
        source={{
          char_end: null,
          char_start: null,
          document_block_id: null,
          id: "cit_stale",
          line_end: null,
          line_start: null,
          page_number: null,
          preview_text: "Archived citation snapshot.",
          source_available: false,
          source_label: "archived.md",
        }}
      />,
    );

    expect(screen.getByText("Snapshot only")).toBeInTheDocument();
    expect(screen.getByText("Archived citation snapshot.")).toBeInTheDocument();
    expect(screen.getByText("Source unavailable")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open source" })).toBeDisabled();
  });
});
