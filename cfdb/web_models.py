from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Progress = Literal["unattempted", "attempted", "solved"]
Priority = Literal["critical", "high", "normal", "low"]


class ProblemTagModel(BaseModel):
    tag: str
    importance: Literal["primary", "secondary", "incidental"]
    source: str
    evidence: str | None = None
    solution_variant: str | None = None


class UserStateModel(BaseModel):
    problem_uid: str
    favorite: bool
    note: str
    manual_progress: Progress | None = None
    synced_progress: Progress | None = None
    progress_status: Progress
    priority: Priority | None = None
    progress_synced_at: str | None = None
    updated_at: str | None = None


class UserStatePatch(BaseModel):
    favorite: bool | None = None
    note: str | None = None
    manual_progress: Progress | None = None
    priority: Priority | None = None


class SearchProblemModel(BaseModel):
    problem_uid: str
    contest_id: int
    problem_index: str
    label: str
    title: str
    rating: int | None
    rating_status: str
    canonical_url: str
    problemset_url: str
    contest_title: str
    start_time_utc: str | None = None
    favorite: bool
    manual_progress: Progress | None = None
    synced_progress: Progress | None = None
    progress_status: Progress
    priority: Priority | None = None
    tags: list[ProblemTagModel]


class SearchSummaryModel(BaseModel):
    total: int
    solved: int
    attempted: int
    unattempted: int
    favorites: int
    max_rating: int | None = None


class SearchFacetsModel(BaseModel):
    favorite: dict[str, int]
    progress: dict[str, int]
    priority: dict[str, int]
    tag_counts: dict[str, int]


class SearchResponseModel(BaseModel):
    items: list[SearchProblemModel]
    total: int
    limit: int
    offset: int
    summary: SearchSummaryModel
    facets: SearchFacetsModel


class TagNodeModel(BaseModel):
    tag: str
    display_name: str
    description: str
    status: str
    problem_count: int
    children: list["TagNodeModel"] = Field(default_factory=list)


class AnnotationModel(BaseModel):
    summary: str
    constraints: str
    core_idea: str
    complexity: str
    tricks: list[object]
    confidence: str | None = None
    review_status: str | None = None
    last_reviewed_at: str | None = None


class SolutionVariantModel(BaseModel):
    variant_name: str
    summary: str | None = None
    complexity: str | None = None
    confidence: str
    is_primary: bool


class SourceModel(BaseModel):
    source_type: str
    url: str
    fetched_at: str | None = None
    notes: str | None = None


class AliasModel(BaseModel):
    alias_problem_uid: str
    alias_contest_id: int
    alias_problem_index: str
    reason: str


class ProblemDetailModel(BaseModel):
    problem_uid: str
    contest_id: int
    problem_index: str
    label: str
    title: str
    contest_title: str
    start_time_utc: str | None = None
    rating: int | None
    rating_status: str
    canonical_url: str
    problemset_url: str
    official_tags: list[object]
    annotation: AnnotationModel
    tags: list[ProblemTagModel]
    solution_variants: list[SolutionVariantModel]
    sources: list[SourceModel]
    aliases: list[AliasModel]
    user_state: UserStateModel


class SettingsModel(BaseModel):
    codeforces_handle: str
    locale: Literal["zh", "en"]
    page_size: Literal[20, 50, 100]
    density: Literal["comfortable", "compact"]
    last_submission_id: int | None = None
    last_sync_at: str | None = None
    last_sync_error: str | None = None
    updated_at: str | None = None


class SettingsPatch(BaseModel):
    codeforces_handle: str | None = None
    locale: Literal["zh", "en"] | None = None
    page_size: Literal[20, 50, 100] | None = None
    density: Literal["comfortable", "compact"] | None = None


class SyncRequest(BaseModel):
    full: bool = False


class SyncResultModel(BaseModel):
    mode: Literal["full", "incremental"]
    handle: str
    submissions_processed: int
    matched_problems: int
    attempted: int
    solved: int
    last_submission_id: int | None = None
    last_sync_at: str


class ChartDatumModel(BaseModel):
    name: str | None = None
    tag: str | None = None
    rating: int | None = None
    count: int


class AnalyticsModel(BaseModel):
    scope: Literal["current", "global"]
    summary: SearchSummaryModel
    rating_buckets: list[ChartDatumModel]
    progress: list[ChartDatumModel]
    priority: list[ChartDatumModel]
    top_tags: list[ChartDatumModel]
