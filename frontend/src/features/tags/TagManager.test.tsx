import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { TagManager } from "./TagManager";

describe("TagManager", () => {
  it("lists tags and creates a new tag", async () => {
    const user = userEvent.setup();
    render(<TagManager />);

    expect(await screen.findByText("HR")).toBeInTheDocument();
    expect(screen.getByText("People policy")).toBeInTheDocument();
    expect(screen.getByText("1 binding")).toBeInTheDocument();

    await user.type(screen.getByLabelText("Tag name"), "Security");
    await user.type(screen.getByLabelText("Tag description"), "Access policy");
    await user.click(screen.getByRole("button", { name: "Create tag" }));

    expect(await screen.findByText("Security")).toBeInTheDocument();
    expect(screen.getByText("Access policy")).toBeInTheDocument();
  });
});
