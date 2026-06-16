import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ChunkWorkspace } from "./ChunkWorkspace";

describe("ChunkWorkspace", () => {
  it("shows chunks, source locator preview and supports edit ignore verify actions", async () => {
    const user = userEvent.setup();
    render(<ChunkWorkspace />);

    expect(await screen.findAllByText("Leave requests need approval.")).not.toHaveLength(0);
    expect(screen.getByText("Lines 1-3")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open source" })).toHaveAttribute(
      "href",
      "/files?file_id=file_policy&source_span_id=span_policy&line_start=1&line_end=3",
    );

    await user.clear(screen.getByLabelText("编辑内容"));
    await user.type(screen.getByLabelText("编辑内容"), "Leave requests require manager approval.");
    await user.click(screen.getByRole("button", { name: "保存" }));
    await waitFor(() => expect(screen.getByText("Leave requests require manager approval.")).toBeInTheDocument());

    await user.click(screen.getByRole("button", { name: "忽略" }));
    await waitFor(() => expect(screen.getByText("ignored")).toBeInTheDocument());

    await user.click(screen.getByRole("button", { name: "验证" }));
    await waitFor(() => expect(screen.getByText("verified")).toBeInTheDocument());
  });
});
