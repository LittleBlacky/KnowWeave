import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { FeedbackDialog } from "./FeedbackDialog";

describe("FeedbackDialog", () => {
  it("submits unified feedback and can convert it to an evaluation sample", async () => {
    const user = userEvent.setup();
    render(<FeedbackDialog targetId="wiki_policy" targetType="wiki_page" />);

    await user.selectOptions(screen.getByLabelText("Feedback type"), "wiki_needs_update");
    await user.type(screen.getByLabelText("Feedback comment"), "Clarify manager approval timing.");
    await user.click(screen.getByRole("button", { name: "Submit feedback" }));

    expect(await screen.findByText("feedback_wiki_policy")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Create evaluation candidate" }));

    expect(await screen.findByText("eval_leave_approval")).toBeInTheDocument();
  });
});
