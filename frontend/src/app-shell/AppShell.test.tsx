import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AppShell } from "./AppShell";

vi.mock("next/navigation", () => ({
  usePathname: () => "/chunks",
}));

describe("AppShell", () => {
  it("renders primary navigation, content and context panel", () => {
    render(
      <AppShell>
        <section>Workbench content</section>
      </AppShell>,
    );

    expect(screen.getByText("KnowWeave")).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Primary" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Chunks/ })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByText("Workbench content")).toBeInTheDocument();
    expect(screen.getByText("Retrieved Contexts")).toBeInTheDocument();
  });
});
