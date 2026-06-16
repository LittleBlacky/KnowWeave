import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AppShell } from "./AppShell";

vi.mock("next/navigation", () => ({
  usePathname: () => "/chunks",
  useRouter: () => ({ push: vi.fn() }),
}));

describe("AppShell", () => {
  it("renders primary navigation and content area", () => {
    render(
      <AppShell>
        <section>Workbench content</section>
      </AppShell>,
    );

    expect(screen.getByText("KnowWeave")).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Primary" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /知识分块/ })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByText("Workbench content")).toBeInTheDocument();
  });
});
