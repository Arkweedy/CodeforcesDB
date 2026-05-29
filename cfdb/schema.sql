PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS contests (
    contest_id INTEGER PRIMARY KEY,
    contest_uid TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    phase TEXT,
    cf_type TEXT,
    start_time_seconds INTEGER,
    start_time_utc TEXT,
    duration_seconds INTEGER,
    contest_type TEXT,
    eligibility_status TEXT NOT NULL DEFAULT 'needs_manual_review'
        CHECK (eligibility_status IN ('eligible', 'excluded', 'needs_manual_review')),
    manual_override TEXT
        CHECK (manual_override IN ('manual_include', 'manual_exclude') OR manual_override IS NULL),
    exclusion_reason TEXT,
    extraction_status TEXT NOT NULL DEFAULT 'queued'
        CHECK (extraction_status IN ('queued', 'metadata_loaded', 'problems_loaded', 'excluded', 'failed')),
    last_checked_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS problems (
    problem_uid TEXT PRIMARY KEY,
    contest_id INTEGER NOT NULL REFERENCES contests(contest_id) ON DELETE CASCADE,
    problem_index TEXT NOT NULL,
    title TEXT NOT NULL,
    problem_type TEXT,
    points REAL,
    rating INTEGER,
    rating_status TEXT NOT NULL DEFAULT 'unknown'
        CHECK (rating_status IN ('official', 'pending_cf_rating', 'no_cf_rating', 'unknown')),
    rating_source TEXT,
    rating_last_checked_at TEXT,
    next_rating_check_at TEXT,
    canonical_url TEXT NOT NULL,
    problemset_url TEXT NOT NULL,
    official_tags_json TEXT NOT NULL DEFAULT '[]',
    estimated_rating INTEGER,
    canonical_problem_uid TEXT,
    dedupe_status TEXT NOT NULL DEFAULT 'canonical',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (contest_id, problem_index)
);

CREATE TABLE IF NOT EXISTS problem_aliases (
    alias_problem_uid TEXT PRIMARY KEY,
    canonical_problem_uid TEXT NOT NULL REFERENCES problems(problem_uid) ON DELETE CASCADE,
    alias_contest_id INTEGER NOT NULL,
    alias_problem_index TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS problem_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_uid TEXT NOT NULL REFERENCES problems(problem_uid) ON DELETE CASCADE,
    source_type TEXT NOT NULL,
    url TEXT NOT NULL,
    fetched_at TEXT,
    notes TEXT,
    UNIQUE (problem_uid, source_type, url)
);

CREATE TABLE IF NOT EXISTS problem_annotations (
    problem_uid TEXT PRIMARY KEY REFERENCES problems(problem_uid) ON DELETE CASCADE,
    summary TEXT,
    constraints_text TEXT,
    core_idea TEXT,
    complexity TEXT,
    tricks_json TEXT NOT NULL DEFAULT '[]',
    confidence TEXT NOT NULL DEFAULT 'low'
        CHECK (confidence IN ('low', 'medium', 'high')),
    review_status TEXT NOT NULL DEFAULT 'raw'
        CHECK (review_status IN ('raw', 'auto_seeded', 'reviewed', 'verified', 'excluded', 'needs_manual_review')),
    last_reviewed_at TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS solution_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_uid TEXT NOT NULL REFERENCES problems(problem_uid) ON DELETE CASCADE,
    variant_name TEXT NOT NULL,
    summary TEXT,
    complexity TEXT,
    confidence TEXT NOT NULL DEFAULT 'low'
        CHECK (confidence IN ('low', 'medium', 'high')),
    is_primary INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (problem_uid, variant_name)
);

CREATE TABLE IF NOT EXISTS tags (
    tag TEXT PRIMARY KEY,
    display_name TEXT,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'candidate'
        CHECK (status IN ('candidate', 'active', 'deprecated')),
    created_from_problem TEXT,
    created_reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tag_edges (
    parent_tag TEXT NOT NULL REFERENCES tags(tag) ON DELETE CASCADE,
    child_tag TEXT NOT NULL REFERENCES tags(tag) ON DELETE CASCADE,
    PRIMARY KEY (parent_tag, child_tag),
    CHECK (parent_tag <> child_tag)
);

CREATE TABLE IF NOT EXISTS tag_aliases (
    alias TEXT PRIMARY KEY,
    tag TEXT NOT NULL REFERENCES tags(tag) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS problem_tags (
    problem_uid TEXT NOT NULL REFERENCES problems(problem_uid) ON DELETE CASCADE,
    tag TEXT NOT NULL REFERENCES tags(tag) ON DELETE CASCADE,
    importance TEXT NOT NULL CHECK (importance IN ('primary', 'secondary', 'incidental')),
    evidence TEXT,
    source TEXT NOT NULL DEFAULT 'manual',
    solution_variant_id INTEGER REFERENCES solution_variants(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (problem_uid, tag, importance, source)
);

CREATE TABLE IF NOT EXISTS problem_user_state (
    problem_uid TEXT PRIMARY KEY REFERENCES problems(problem_uid) ON DELETE CASCADE,
    favorite INTEGER NOT NULL DEFAULT 0 CHECK (favorite IN (0, 1)),
    note TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ingestion_queue (
    contest_id INTEGER PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'in_progress', 'done', 'skipped', 'failed')),
    priority INTEGER NOT NULL DEFAULT 100,
    last_error TEXT,
    queued_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rating_refresh_queue (
    problem_uid TEXT PRIMARY KEY REFERENCES problems(problem_uid) ON DELETE CASCADE,
    contest_id INTEGER NOT NULL,
    problem_index TEXT NOT NULL,
    next_check_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'done', 'expired', 'failed')),
    last_error TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_contests_extract_order
    ON contests(eligibility_status, extraction_status, start_time_seconds, contest_id);

CREATE INDEX IF NOT EXISTS idx_problems_rating
    ON problems(rating_status, rating, contest_id, problem_index);

CREATE INDEX IF NOT EXISTS idx_problem_tags_tag
    ON problem_tags(tag, importance, problem_uid);

CREATE INDEX IF NOT EXISTS idx_problem_tags_problem
    ON problem_tags(problem_uid, importance);

CREATE INDEX IF NOT EXISTS idx_problem_user_state_favorite
    ON problem_user_state(favorite, problem_uid);
