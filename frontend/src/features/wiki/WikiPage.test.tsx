import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { WikiPage } from "./WikiPage";

describe("WikiPage", () => {
  it("loads wiki detail, shows citations and saves an edit with a change summary", async () => {
    const user = userEvent.setup();
    render(<WikiPage />);

    expect(await screen.findByText("policy.md")).toBeInTheDocument();
    expect(screen.getByText("draft")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /policy\.md/i }));

    expect(await screen.findByText(/Leave requests require manager approval/)).toBeInTheDocument();
    expect(screen.getByText("S1")).toBeInTheDocument();

    await user.clear(screen.getByLabelText("Markdown 正文"));
    await user.type(screen.getByLabelText("Markdown 正文"), "Updated wiki content.");
    await user.type(screen.getByLabelText("变更说明"), "Clarified manager approval policy.");
    await user.click(screen.getByRole("button", { name: "保存修改" }));

    expect(await screen.findByText("Updated wiki content.")).toBeInTheDocument();
  });
});
