import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { FileList } from "./FileList";

describe("FileList", () => {
  it("lists files and can parse then build chunks for a file", async () => {
    const user = userEvent.setup();
    render(<FileList refreshKey={0} />);

    expect(await screen.findByText("policy.md")).toBeInTheDocument();
    expect(screen.getByText("uploaded")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Parse policy.md" }));
    await waitFor(() => expect(screen.getByText("parse_succeeded")).toBeInTheDocument());

    await user.click(screen.getByRole("button", { name: "Build chunks for policy.md" }));
    await waitFor(() => expect(screen.getByText("1 chunks built")).toBeInTheDocument());
  });
});
