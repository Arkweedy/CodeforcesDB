import { describe, expect, it } from "vitest";
import { DEFAULT_SEARCH, readUrlState, writeUrlState } from "./urlState";

describe("URL search state", () => {
  it("round-trips filters, sorting, paging and detail selection", () => {
    const state = {
      ...DEFAULT_SEARCH,
      tags: ["dp", "graph/tree"],
      excludeTags: ["implementation"],
      progressStatuses: ["attempted" as const, "solved" as const],
      priorities: ["critical" as const],
      favorite: "favorite" as const,
      sortBy: "priority" as const,
      sortOrder: "desc" as const,
      page: 3,
      pageSize: 20 as const,
      problemUid: "cf_problem:100:A"
    };
    writeUrlState(state);
    expect(readUrlState()).toEqual(state);
  });

  it("normalizes invalid values", () => {
    const state = readUrlState("?page=-5&limit=13&sort_by=nope&tag_mode=nope");
    expect(state.page).toBe(1);
    expect(state.pageSize).toBe(50);
    expect(state.sortBy).toBe("rating");
    expect(state.tagMode).toBe("and");
  });

  it("round-trips intentionally empty rating and importance filters", () => {
    const state = { ...DEFAULT_SEARCH, ratingStatuses: [], importance: [] };
    writeUrlState(state);
    expect(readUrlState().ratingStatuses).toEqual([]);
    expect(readUrlState().importance).toEqual([]);
  });
});
