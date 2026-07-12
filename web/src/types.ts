export type Importance = "primary" | "secondary" | "incidental";
export type RatingStatus = "official" | "pending_cf_rating" | "no_cf_rating" | "unknown";
export type TagMode = "and" | "or";
export type ProgressStatus = "unattempted" | "attempted" | "solved";
export type Priority = "critical" | "high" | "normal" | "low";
export type FavoriteFilter = "any" | "favorite" | "not_favorite";
export type SortBy = "problem" | "title" | "rating" | "progress" | "priority" | "favorite";
export type SortOrder = "asc" | "desc";
export type Locale = "zh" | "en";
export type Density = "comfortable" | "compact";

export interface TagNode {
  tag: string;
  display_name: string;
  description: string;
  status: string;
  problem_count: number;
  children: TagNode[];
}

export interface ProblemTag {
  tag: string;
  importance: Importance;
  evidence?: string;
  source: string;
  solution_variant?: string;
}

export interface UserState {
  problem_uid: string;
  favorite: boolean;
  note: string;
  manual_progress: ProgressStatus | null;
  synced_progress: ProgressStatus | null;
  progress_status: ProgressStatus;
  priority: Priority | null;
  progress_synced_at?: string | null;
  updated_at?: string | null;
}

export interface SearchProblem {
  problem_uid: string;
  contest_id: number;
  problem_index: string;
  label: string;
  title: string;
  rating: number | null;
  rating_status: RatingStatus;
  canonical_url: string;
  problemset_url: string;
  contest_title: string;
  start_time_utc?: string;
  favorite: boolean;
  manual_progress: ProgressStatus | null;
  synced_progress: ProgressStatus | null;
  progress_status: ProgressStatus;
  priority: Priority | null;
  tags: ProblemTag[];
}

export interface SearchSummary {
  total: number;
  solved: number;
  attempted: number;
  unattempted: number;
  favorites: number;
  max_rating: number | null;
}

export interface SearchFacets {
  favorite: Record<"all" | "favorite" | "not_favorite", number>;
  progress: Record<ProgressStatus, number>;
  priority: Record<Priority | "unassigned", number>;
  tag_counts: Record<string, number>;
}

export interface SearchResponse {
  items: SearchProblem[];
  total: number;
  limit: number;
  offset: number;
  summary: SearchSummary;
  facets: SearchFacets;
}

export interface ProblemDetail {
  problem_uid: string;
  contest_id: number;
  problem_index: string;
  label: string;
  title: string;
  contest_title: string;
  start_time_utc?: string;
  rating: number | null;
  rating_status: RatingStatus;
  canonical_url: string;
  problemset_url: string;
  official_tags: string[];
  annotation: {
    summary: string;
    constraints: string;
    core_idea: string;
    complexity: string;
    tricks: string[];
    confidence: string | null;
    review_status: string | null;
    last_reviewed_at?: string;
  };
  tags: ProblemTag[];
  solution_variants: Array<{
    variant_name: string;
    summary?: string;
    complexity?: string;
    confidence: string;
    is_primary: boolean;
  }>;
  sources: Array<{
    source_type: string;
    url: string;
    fetched_at?: string;
    notes?: string;
  }>;
  aliases: Array<{
    alias_problem_uid: string;
    alias_contest_id: number;
    alias_problem_index: string;
    reason: string;
  }>;
  user_state: UserState;
}

export interface Settings {
  codeforces_handle: string;
  locale: Locale;
  page_size: 20 | 50 | 100;
  density: Density;
  last_submission_id: number | null;
  last_sync_at: string | null;
  last_sync_error: string | null;
  updated_at?: string;
}

export interface SyncResult {
  mode: "full" | "incremental";
  handle: string;
  submissions_processed: number;
  matched_problems: number;
  attempted: number;
  solved: number;
  last_submission_id: number | null;
  last_sync_at: string;
}

export interface ChartDatum {
  name?: string;
  tag?: string;
  rating?: number;
  count: number;
}

export interface Analytics {
  scope: "current" | "global";
  summary: SearchSummary;
  rating_buckets: ChartDatum[];
  progress: ChartDatum[];
  priority: ChartDatum[];
  top_tags: ChartDatum[];
}

export interface SearchParams {
  ratingMin: string;
  ratingMax: string;
  ratingStatuses: RatingStatus[];
  importance: Importance[];
  tags: string[];
  excludeTags: string[];
  tagMode: TagMode;
  favorite: FavoriteFilter;
  progressStatuses: ProgressStatus[];
  priorities: Array<Priority | "unassigned">;
  query: string;
  sortBy: SortBy;
  sortOrder: SortOrder;
  page: number;
  pageSize: 20 | 50 | 100;
  problemUid: string | null;
}

export interface Stats {
  canonical_problems: number;
  reviewed_problems: number;
  tags: number;
  favorites: number;
}
