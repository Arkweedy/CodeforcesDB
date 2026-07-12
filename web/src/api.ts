import type {
  Analytics,
  ProblemDetail,
  SearchParams,
  SearchResponse,
  Settings,
  SyncResult,
  TagNode,
  UserState
} from "./types";

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail || response.statusText || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function searchQuery(params: SearchParams, includePage = true): string {
  const query = new URLSearchParams();
  if (params.ratingMin) query.set("rating_min", params.ratingMin);
  if (params.ratingMax) query.set("rating_max", params.ratingMax);
  params.ratingStatuses.forEach((value) => query.append("rating_status", value));
  params.importance.forEach((value) => query.append("importance", value));
  params.tags.forEach((value) => query.append("tags", value));
  params.excludeTags.forEach((value) => query.append("exclude", value));
  params.progressStatuses.forEach((value) => query.append("progress_status", value));
  params.priorities.forEach((value) => query.append("priority", value));
  query.set("tag_mode", params.tagMode);
  query.set("favorite", params.favorite);
  if (params.query.trim()) query.set("q", params.query.trim());
  query.set("sort_by", params.sortBy);
  query.set("sort_order", params.sortOrder);
  if (includePage) {
    query.set("limit", String(params.pageSize));
    query.set("offset", String((params.page - 1) * params.pageSize));
  }
  return query.toString();
}

export const api = {
  tags: (signal?: AbortSignal) => requestJson<TagNode[]>("/api/tags", { signal }),
  search: (params: SearchParams, signal?: AbortSignal) =>
    requestJson<SearchResponse>(`/api/search?${searchQuery(params)}`, { signal }),
  problem: (problemUid: string, signal?: AbortSignal) =>
    requestJson<ProblemDetail>(`/api/problems/${encodeURIComponent(problemUid)}`, { signal }),
  analytics: (params: SearchParams, scope: "current" | "global", signal?: AbortSignal) =>
    requestJson<Analytics>(
      `/api/analytics?scope=${scope}&${searchQuery(params, false)}`,
      { signal }
    ),
  settings: (signal?: AbortSignal) => requestJson<Settings>("/api/settings", { signal }),
  patchSettings: (changes: Partial<Pick<Settings, "codeforces_handle" | "locale" | "page_size" | "density">>) =>
    requestJson<Settings>("/api/settings", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(changes)
    }),
  patchUserState: (
    problemUid: string,
    changes: Partial<Pick<UserState, "favorite" | "note" | "manual_progress" | "priority">>
  ) => requestJson<UserState>(`/api/problems/${encodeURIComponent(problemUid)}/user-state`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(changes)
  }),
  syncCodeforces: (full: boolean) => requestJson<SyncResult>("/api/sync/codeforces", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ full })
  })
};
