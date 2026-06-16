import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { SearchPage } from "./SearchPage";

describe("SearchPage", () => {
  it("runs keyword search and shows retrieval run, result and source locator", async () => {
    const user = userEvent.setup();
    render(<SearchPage />);

    await user.clear(screen.getByLabelText("搜索关键词"));
    await user.type(screen.getByLabelText("搜索关键词"), "approval");
    expect(screen.getByLabelText("文件")).toBeChecked();
    expect(screen.getByLabelText("分块")).toBeChecked();
    expect(screen.getByLabelText("知识单元")).toBeChecked();
    expect(screen.getByLabelText("Wiki")).toBeChecked();
    await user.click(screen.getByRole("button", { name: "搜索" }));

    expect(await screen.findByText("run_search_001")).toBeInTheDocument();
    expect(screen.getByText("policy.md")).toBeInTheDocument();
    expect(screen.getByText("Leave requests need approval.")).toBeInTheDocument();
    expect(screen.getByText("选择一个结果查看来源定位")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /policy\.md/i }));

    expect(screen.getByText("Lines 1-3")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open source" })).toHaveAttribute(
      "href",
      "/files?file_id=file_policy&source_span_id=span_policy&line_start=1&line_end=3",
    );
  });
});
