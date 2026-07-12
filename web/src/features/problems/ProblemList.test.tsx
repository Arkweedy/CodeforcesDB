import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DEFAULT_SEARCH } from "../../shared/urlState";
import type { SearchResponse } from "../../types";
import { ProblemList } from "./ProblemList";

const data: SearchResponse = {
  items: [{
    problem_uid: "cf_problem:100:A",
    contest_id: 100,
    problem_index: "A",
    label: "100A",
    title: "Alpha",
    rating: 1500,
    rating_status: "official",
    canonical_url: "https://codeforces.com/contest/100/problem/A",
    problemset_url: "https://codeforces.com/problemset/problem/100/A",
    contest_title: "Round 100",
    favorite: false,
    manual_progress: null,
    synced_progress: null,
    progress_status: "unattempted",
    priority: null,
    tags: [{ tag: "dp", importance: "primary", source: "ai_reviewed" }]
  }],
  total: 1,
  limit: 50,
  offset: 0,
  summary: { total: 1, solved: 0, attempted: 0, unattempted: 1, favorites: 0, max_rating: 1500 },
  facets: {
    favorite: { all: 1, favorite: 0, not_favorite: 1 },
    progress: { unattempted: 1, attempted: 0, solved: 0 },
    priority: { critical: 0, high: 0, normal: 0, low: 0, unassigned: 1 },
    tag_counts: { dp: 1 }
  }
};

describe("ProblemList", () => {
  it("opens a problem and toggles favorite inline", () => {
    const onOpen = vi.fn();
    const onPatch = vi.fn();
    render(<ProblemList data={data} params={DEFAULT_SEARCH} locale="zh" loading={false} selectedUid={null} onChangeParams={vi.fn()} onOpen={onOpen} onPatch={onPatch} />);
    fireEvent.click(screen.getAllByText("Alpha")[0]);
    expect(onOpen).toHaveBeenCalledWith("cf_problem:100:A");
    fireEvent.click(screen.getAllByLabelText("切换收藏")[0]);
    expect(onPatch).toHaveBeenCalledWith("cf_problem:100:A", { favorite: true });
  });

  it("emits pagination changes", () => {
    const onChangeParams = vi.fn();
    render(<ProblemList data={{ ...data, total: 120 }} params={DEFAULT_SEARCH} locale="zh" loading={false} selectedUid={null} onChangeParams={onChangeParams} onOpen={vi.fn()} onPatch={vi.fn()} />);
    fireEvent.click(screen.getByText("2"));
    expect(onChangeParams).toHaveBeenCalledWith({ page: 2 });
  });
});
