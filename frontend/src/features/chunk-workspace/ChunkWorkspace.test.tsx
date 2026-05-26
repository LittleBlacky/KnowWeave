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

    await user.clear(screen.getByLabelText("Edited chunk content"));
    await user.type(screen.getByLabelText("Edited chunk content"), "Leave requests require manager approval.");
    await user.click(screen.getByRole("button", { name: "Save chunk edits" }));
    await waitFor(() => expect(screen.getByText("Edited")).toBeInTheDocument());

    await user.click(screen.getByRole("button", { name: "Ignore chunk" }));
    await waitFor(() => expect(screen.getByText("ignored")).toBeInTheDocument());

    await user.click(screen.getByRole("button", { name: "Verify chunk" }));
    await waitFor(() => expect(screen.getByText("verified")).toBeInTheDocument());
  });
});
