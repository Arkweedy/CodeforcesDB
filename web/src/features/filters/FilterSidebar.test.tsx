import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DEFAULT_SEARCH } from "../../shared/urlState";
import { FilterSidebar } from "./FilterSidebar";

describe("FilterSidebar", () => {
  it("emits search and reset actions", () => {
    const onChange = vi.fn();
    const onReset = vi.fn();
    render(<FilterSidebar tagTree={[]} params={DEFAULT_SEARCH} locale="zh" onChange={onChange} onReset={onReset} />);
    fireEvent.change(screen.getByPlaceholderText("题目标题 / 编号 / 标签"), { target: { value: "1705D" } });
    expect(onChange).toHaveBeenCalledWith({ query: "1705D" });
    fireEvent.click(screen.getByText("重置"));
    expect(onReset).toHaveBeenCalled();
  });
});
