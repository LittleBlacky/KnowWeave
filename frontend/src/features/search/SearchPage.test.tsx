import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { SearchPage } from "./SearchPage";

describe("SearchPage", () => {
  it("runs keyword search and shows retrieval run, result and source locator", async () => {
    const user = userEvent.setup();
    render(<SearchPage />);

    await user.clear(screen.getByLabelText("Search query"));
    await user.type(screen.getByLabelText("Search query"), "approval");
    expect(screen.getByLabelText("Files")).toBeChecked();
    expect(screen.getByLabelText("Chunks")).toBeChecked();
    expect(screen.getByLabelText("Knowledge Units")).toBeChecked();
    expect(screen.getByLabelText("Wiki Pages")).toBeChecked();
    await user.click(screen.getByRole("button", { name: "Run search" }));

    expect(await screen.findByText("run_search_001")).toBeInTheDocument();
    expect(screen.getByText("policy.md")).toBeInTheDocument();
    expect(screen.getByText("Leave requests need approval.")).toBeInTheDocument();
    expect(screen.getByText("Select a result to inspect its source locator.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /policy\.md/i }));

    expect(screen.getByText("Lines 1-3")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open source" })).toHaveAttribute(
      "href",
      "/files?file_id=file_policy&source_span_id=span_policy&line_start=1&line_end=3",
    );
  });
});
