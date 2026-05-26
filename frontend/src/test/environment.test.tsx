import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

function TestWorkbenchLabel() {
  return <div>KnowWeave test workbench</div>;
}

describe("frontend test environment", () => {
  it("renders React components with Testing Library matchers", () => {
    render(<TestWorkbenchLabel />);

    expect(screen.getByText("KnowWeave test workbench")).toBeInTheDocument();
  });

  it("serves API fixtures through MSW", async () => {
    const response = await fetch("http://localhost/api/v1/health");

    await expect(response.json()).resolves.toMatchObject({
      status: "ok",
      service: "knowweave-frontend-msw",
    });
  });
});
