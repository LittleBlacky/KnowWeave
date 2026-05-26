import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ChatPage } from "./ChatPage";

describe("ChatPage", () => {
  it("creates a session, streams an answer and shows citations with source preview", async () => {
    const user = userEvent.setup();
    render(<ChatPage />);

    await user.type(screen.getByLabelText("Chat question"), "approval");
    await user.click(screen.getByRole("button", { name: "Send question" }));

    expect(await screen.findByText("run_chat_001")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText(/Fake answer: approval/)).toBeInTheDocument());
    expect(screen.getByText("S1")).toBeInTheDocument();
    expect(screen.getByText("Leave requests need approval.")).toBeInTheDocument();
    expect(screen.getByText("Select a citation to inspect its source locator.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /S1/ }));

    expect(screen.getByText("Lines 1-3")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open source" })).toHaveAttribute(
      "href",
      "/files?file_id=file_policy&source_span_id=span_policy&line_start=1&line_end=3",
    );
  });
});
