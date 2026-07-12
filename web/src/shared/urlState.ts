import type {
  FavoriteFilter,
  Importance,
  Priority,
  ProgressStatus,
  RatingStatus,
  SearchParams,
  SortBy,
  SortOrder,
  TagMode
} from "../types";

const RATINGS: RatingStatus[] = ["official", "pending_cf_rating", "no_cf_rating", "unknown"];
const IMPORTANCE: Importance[] = ["primary", "secondary", "incidental"];
const PROGRESS: ProgressStatus[] = ["unattempted", "attempted", "solved"];
const PRIORITIES: Array<Priority | "unassigned"> = ["critical", "high", "normal", "low", "unassigned"];
const SORTS: SortBy[] = ["problem", "title", "rating", "progress", "priority", "favorite"];

export const DEFAULT_SEARCH: SearchParams = {
  ratingMin: "",
  ratingMax: "",
  ratingStatuses: ["official"],
  importance: ["primary", "secondary"],
  tags: [],
  excludeTags: [],
  tagMode: "and",
  favorite: "any",
  progressStatuses: [],
  priorities: [],
  query: "",
  sortBy: "rating",
  sortOrder: "asc",
  page: 1,
  pageSize: 50,
  problemUid: null
};

function list<T extends string>(query: URLSearchParams, key: string, values: readonly T[]): T[] {
  return query.getAll(key).filter((value): value is T => values.includes(value as T));
}

export function readUrlState(search = window.location.search): SearchParams {
  const query = new URLSearchParams(search);
  const pageSize = Number(query.get("limit"));
  const favorite = query.get("favorite") as FavoriteFilter | null;
  const tagMode = query.get("tag_mode") as TagMode | null;
  const sortBy = query.get("sort_by") as SortBy | null;
  const sortOrder = query.get("sort_order") as SortOrder | null;
  return {
    ratingMin: query.get("rating_min") ?? "",
    ratingMax: query.get("rating_max") ?? "",
    ratingStatuses: query.has("rating_status") ? list(query, "rating_status", RATINGS) : ["official"],
    importance: query.has("importance") ? list(query, "importance", IMPORTANCE) : ["primary", "secondary"],
    tags: query.getAll("tags"),
    excludeTags: query.getAll("exclude"),
    tagMode: tagMode === "or" ? "or" : "and",
    favorite: favorite === "favorite" || favorite === "not_favorite" ? favorite : "any",
    progressStatuses: list(query, "progress_status", PROGRESS),
    priorities: list(query, "priority", PRIORITIES),
    query: query.get("q") ?? "",
    sortBy: sortBy && SORTS.includes(sortBy) ? sortBy : "rating",
    sortOrder: sortOrder === "desc" ? "desc" : "asc",
    page: Math.max(1, Number(query.get("page")) || 1),
    pageSize: pageSize === 20 || pageSize === 100 ? pageSize : 50,
    problemUid: query.get("problem")
  };
}

export function writeUrlState(params: SearchParams): void {
  const query = new URLSearchParams();
  if (params.ratingMin) query.set("rating_min", params.ratingMin);
  if (params.ratingMax) query.set("rating_max", params.ratingMax);
  if (params.ratingStatuses.length === 0) query.set("rating_status", "");
  else params.ratingStatuses.forEach((value) => query.append("rating_status", value));
  if (params.importance.length === 0) query.set("importance", "");
  else params.importance.forEach((value) => query.append("importance", value));
  params.tags.forEach((value) => query.append("tags", value));
  params.excludeTags.forEach((value) => query.append("exclude", value));
  params.progressStatuses.forEach((value) => query.append("progress_status", value));
  params.priorities.forEach((value) => query.append("priority", value));
  if (params.tagMode !== "and") query.set("tag_mode", params.tagMode);
  if (params.favorite !== "any") query.set("favorite", params.favorite);
  if (params.query.trim()) query.set("q", params.query.trim());
  if (params.sortBy !== "rating") query.set("sort_by", params.sortBy);
  if (params.sortOrder !== "asc") query.set("sort_order", params.sortOrder);
  if (params.page !== 1) query.set("page", String(params.page));
  if (params.pageSize !== 50) query.set("limit", String(params.pageSize));
  if (params.problemUid) query.set("problem", params.problemUid);
  const suffix = query.toString();
  window.history.replaceState(null, "", `${window.location.pathname}${suffix ? `?${suffix}` : ""}`);
}

export function toggleValue<T>(values: T[], value: T): T[] {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}
