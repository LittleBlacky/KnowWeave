import {render, screen} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {describe, expect, it} from "vitest";

import {KnowledgeUnitPage} from "./KnowledgeUnitPage";

describe("KnowledgeUnitPage", () => {
  it("lists knowledge units, shows sources and verifies a sourced unit", async () => {
    const user = userEvent.setup();
    render(<KnowledgeUnitPage />);

    expect(await screen.findByText("Leave approval rule")).toBeInTheDocument();
    expect(screen.getByText("pending_review")).toBeInTheDocument();
    expect(screen.getByText("HR")).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", {name: /Leave approval rule/i}),
    );

    expect(
      await screen.findByText("Leave requests require manager approval."),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", {name: "确认"}));

    // After verification, the status badge in the list changes to "verified"
    // Both the list card and detail panel may show the badge
    expect(await screen.findAllByText("verified")).not.toHaveLength(0);
  });
});

