import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { FileUpload } from "./FileUpload";

describe("FileUpload", () => {
  it("uploads a selected file and reports the created record", async () => {
    const user = userEvent.setup();
    const uploaded: string[] = [];
    render(<FileUpload onUploaded={(file) => uploaded.push(file.name)} />);

    const input = screen.getByLabelText("Upload evidence file");
    await user.upload(input, new File(["# Policy"], "policy.md", { type: "text/markdown" }));

    await waitFor(() => expect(uploaded).toEqual(["policy.md"]));
    expect(screen.getByText("Uploaded policy.md")).toBeInTheDocument();
  });
});
