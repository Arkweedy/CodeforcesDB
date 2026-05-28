import type {
  Importance,
  ProblemDetail,
  RatingStatus,
  SearchResponse,
  Stats,
  TagMode,
  TagNode
} from "./types";

async function getJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return (await response.json()) as T;
}

export interface SearchParams {
  ratingMin?: string;
  ratingMax?: string;
  ratingStatuses: RatingStatus[];
  importance: Importance[];
  tags: string[];
  tagMode: TagMode;
  favoriteOnly: boolean;
  query: string;
}

export function fetchTags(): Promise<TagNode[]> {
  return getJson<TagNode[]>("/api/tags");
}

export function fetchStats(): Promise<Stats> {
  return getJson<Stats>("/api/stats");
}

export function fetchSearch(params: SearchParams): Promise<SearchResponse> {
  const query = new URLSearchParams();
  if (params.ratingMin) query.set("rating_min", params.ratingMin);
  if (params.ratingMax) query.set("rating_max", params.ratingMax);
  params.ratingStatuses.forEach((item) => query.append("rating_status", item));
  params.importance.forEach((item) => query.append("importance", item));
  params.tags.forEach((item) => query.append("tags", item));
  query.set("tag_mode", params.tagMode);
  if (params.favoriteOnly) query.set("favorite_only", "true");
  if (params.query.trim()) query.set("q", params.query.trim());
  query.set("limit", "200");
  return getJson<SearchResponse>(`/api/search?${query.toString()}`);
}

export function fetchProblem(problemUid: string): Promise<ProblemDetail> {
  return getJson<ProblemDetail>(`/api/problems/${encodeURIComponent(problemUid)}`);
}

export function saveUserState(
  problemUid: string,
  favorite: boolean,
  note: string
): Promise<ProblemDetail["user_state"]> {
  return getJson<ProblemDetail["user_state"]>(
    `/api/problems/${encodeURIComponent(problemUid)}/user-state`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ favorite, note })
    }
  );
}
