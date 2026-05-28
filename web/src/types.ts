export type Importance = "primary" | "secondary" | "incidental";
export type RatingStatus = "official" | "pending_cf_rating" | "no_cf_rating" | "unknown";
export type TagMode = "and" | "or";

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

export interface SearchProblem {
  problem_uid: string;
  contest_id: number;
  problem_index: string;
  label: string;
  title: string;
  rating: number | null;
  rating_status: RatingStatus;
  canonical_url: string;
  contest_title: string;
  start_time_utc?: string;
  favorite: boolean;
  tags: ProblemTag[];
}

export interface SearchResponse {
  items: SearchProblem[];
  limit: number;
  offset: number;
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
    confidence: string;
    review_status: string;
    last_reviewed_at?: string;
  };
  tags: ProblemTag[];
  solution_variants: Array<{
    variant_name: string;
    summary: string;
    complexity: string;
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
  user_state: {
    favorite: boolean;
    note: string;
    updated_at?: string;
  };
}

export interface Stats {
  canonical_problems: number;
  reviewed_problems: number;
  tags: number;
  favorites: number;
}
