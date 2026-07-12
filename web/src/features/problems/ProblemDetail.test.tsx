import * as Tooltip from "@radix-ui/react-tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ProblemDetail } from "./ProblemDetail";

const apiMocks = vi.hoisted(() => ({ problem: vi.fn() }));
vi.mock("../../api", () => ({ api: apiMocks }));

describe("ProblemDetail", () => {
  it("keeps the detail open when discarding a dirty note is rejected", async () => {
    apiMocks.problem.mockResolvedValue({
      problem_uid: "cf_problem:100:A",
      contest_id: 100,
      problem_index: "A",
      label: "100A",
      title: "Alpha",
      contest_title: "Round 100",
      rating: 1500,
      rating_status: "official",
      canonical_url: "https://codeforces.com/contest/100/problem/A",
      problemset_url: "https://codeforces.com/problemset/problem/100/A",
      official_tags: [],
      annotation: { summary: "summary", constraints: "", core_idea: "", complexity: "", tricks: [], confidence: "high", review_status: "reviewed" },
      tags: [],
      solution_variants: [],
      sources: [],
      aliases: [],
      user_state: { problem_uid: "cf_problem:100:A", favorite: false, note: "saved", manual_progress: null, synced_progress: null, progress_status: "unattempted", priority: null }
    });
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    const onClose = vi.fn();
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <Tooltip.Provider>
          <ProblemDetail problemUid="cf_problem:100:A" locale="zh" onClose={onClose} onDirtyChange={vi.fn()} onPatch={vi.fn()} />
        </Tooltip.Provider>
      </QueryClientProvider>
    );
    fireEvent.click(await screen.findByLabelText("编辑笔记"));
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "unsaved" } });
    fireEvent.click(screen.getByLabelText("关闭"));
    expect(confirm).toHaveBeenCalled();
    expect(onClose).not.toHaveBeenCalled();
    confirm.mockRestore();
  });
});
