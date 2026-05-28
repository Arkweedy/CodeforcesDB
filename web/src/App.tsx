import {
  ChevronRight,
  ExternalLink,
  Info,
  Loader2,
  Save,
  Search,
  Star,
  X
} from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  fetchProblem,
  fetchSearch,
  fetchStats,
  fetchTags,
  saveUserState,
  type SearchParams
} from "./api";
import type {
  Importance,
  ProblemDetail,
  ProblemTag,
  RatingStatus,
  SearchProblem,
  Stats,
  TagMode,
  TagNode
} from "./types";

const RATING_STATUSES: RatingStatus[] = [
  "official",
  "pending_cf_rating",
  "no_cf_rating",
  "unknown"
];
const IMPORTANCE_VALUES: Importance[] = ["primary", "secondary", "incidental"];

function toggleValue<T>(values: T[], value: T): T[] {
  return values.includes(value)
    ? values.filter((item) => item !== value)
    : [...values, value];
}

function shortTag(tag: string): string {
  return tag.split("/").slice(-1)[0].replace(/-/g, " ");
}

function byImportance(tags: ProblemTag[], importance: Importance): ProblemTag[] {
  return tags.filter((tag) => tag.importance === importance);
}

function TagTreeItem({
  node,
  selectedTags,
  expanded,
  onToggleExpanded,
  onToggleSelected
}: {
  node: TagNode;
  selectedTags: string[];
  expanded: Set<string>;
  onToggleExpanded: (tag: string) => void;
  onToggleSelected: (tag: string) => void;
}) {
  const hasChildren = node.children.length > 0;
  const isOpen = expanded.has(node.tag);
  const isSelected = selectedTags.includes(node.tag);

  return (
    <div className="tag-node">
      <div className="tag-row">
        <button
          className="icon-button tag-expander"
          disabled={!hasChildren}
          onClick={() => onToggleExpanded(node.tag)}
          aria-label={isOpen ? "collapse" : "expand"}
        >
          {hasChildren ? (
            <ChevronRight className={isOpen ? "rotated" : ""} size={16} />
          ) : (
            <span className="expander-spacer" />
          )}
        </button>
        <label className="tag-check">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => onToggleSelected(node.tag)}
          />
          <span className="tag-name">{node.display_name}</span>
          <span className="tag-count">{node.problem_count}</span>
        </label>
      </div>
      {isOpen && hasChildren ? (
        <div className="tag-children">
          {node.children.map((child) => (
            <TagTreeItem
              key={`${node.tag}:${child.tag}`}
              node={child}
              selectedTags={selectedTags}
              expanded={expanded}
              onToggleExpanded={onToggleExpanded}
              onToggleSelected={onToggleSelected}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}

function FilterPanel({
  tagTree,
  params,
  expanded,
  setParams,
  setExpanded
}: {
  tagTree: TagNode[];
  params: SearchParams;
  expanded: Set<string>;
  setParams: (next: SearchParams) => void;
  setExpanded: (next: Set<string>) => void;
}) {
  const setSelectedTags = (tags: string[]) => setParams({ ...params, tags });
  const toggleExpanded = (tag: string) => {
    const next = new Set(expanded);
    if (next.has(tag)) next.delete(tag);
    else next.add(tag);
    setExpanded(next);
  };

  return (
    <aside className="filters">
      <div className="filter-header">
        <Search size={18} />
        <span>Search</span>
      </div>

      <label className="field">
        <span>Text</span>
        <input
          value={params.query}
          onChange={(event) => setParams({ ...params, query: event.target.value })}
          placeholder="2174D, Secret, dp..."
        />
      </label>

      <div className="rating-grid">
        <label className="field">
          <span>Rating min</span>
          <input
            value={params.ratingMin}
            inputMode="numeric"
            onChange={(event) =>
              setParams({ ...params, ratingMin: event.target.value })
            }
          />
        </label>
        <label className="field">
          <span>Rating max</span>
          <input
            value={params.ratingMax}
            inputMode="numeric"
            onChange={(event) =>
              setParams({ ...params, ratingMax: event.target.value })
            }
          />
        </label>
      </div>

      <div className="segmented">
        {(["and", "or"] as TagMode[]).map((mode) => (
          <button
            key={mode}
            className={params.tagMode === mode ? "active" : ""}
            onClick={() => setParams({ ...params, tagMode: mode })}
          >
            {mode.toUpperCase()}
          </button>
        ))}
      </div>

      <label className="switch-row">
        <input
          type="checkbox"
          checked={params.favoriteOnly}
          onChange={() =>
            setParams({ ...params, favoriteOnly: !params.favoriteOnly })
          }
        />
        <span>Favorites</span>
      </label>

      <section className="check-section">
        <h2>Rating Status</h2>
        {RATING_STATUSES.map((status) => (
          <label key={status} className="check-row">
            <input
              type="checkbox"
              checked={params.ratingStatuses.includes(status)}
              onChange={() =>
                setParams({
                  ...params,
                  ratingStatuses: toggleValue(params.ratingStatuses, status)
                })
              }
            />
            <span>{status}</span>
          </label>
        ))}
      </section>

      <section className="check-section">
        <h2>Importance</h2>
        {IMPORTANCE_VALUES.map((importance) => (
          <label key={importance} className="check-row">
            <input
              type="checkbox"
              checked={params.importance.includes(importance)}
              onChange={() =>
                setParams({
                  ...params,
                  importance: toggleValue(params.importance, importance)
                })
              }
            />
            <span>{importance}</span>
          </label>
        ))}
      </section>

      {params.tags.length ? (
        <div className="selected-tags">
          {params.tags.map((tag) => (
            <button
              key={tag}
              className="tag-chip"
              onClick={() => setSelectedTags(params.tags.filter((item) => item !== tag))}
            >
              {tag}
              <X size={13} />
            </button>
          ))}
        </div>
      ) : null}

      <section className="tag-tree">
        <h2>Tags</h2>
        {tagTree.map((node) => (
          <TagTreeItem
            key={node.tag}
            node={node}
            selectedTags={params.tags}
            expanded={expanded}
            onToggleExpanded={toggleExpanded}
            onToggleSelected={(tag) => setSelectedTags(toggleValue(params.tags, tag))}
          />
        ))}
      </section>
    </aside>
  );
}

function ProblemResult({
  problem,
  onOpen
}: {
  problem: SearchProblem;
  onOpen: (problemUid: string) => void;
}) {
  const visibleTags = problem.tags
    .filter((tag) => tag.importance !== "incidental")
    .slice(0, 5);

  return (
    <article className="result-item">
      <div className="result-main">
        <a
          className="problem-link"
          href={problem.canonical_url}
          target="_blank"
          rel="noreferrer"
        >
          {problem.label} {problem.title}
        </a>
        <button className="icon-button" onClick={() => onOpen(problem.problem_uid)}>
          <Info size={18} />
        </button>
      </div>
      <div className="result-meta">
        <span className="rating">{problem.rating ?? problem.rating_status}</span>
        {problem.favorite ? (
          <span className="favorite-mark">
            <Star size={14} fill="currentColor" /> favorite
          </span>
        ) : null}
        {visibleTags.map((tag) => (
          <span key={`${problem.problem_uid}:${tag.tag}:${tag.importance}`} className="mini-tag">
            {shortTag(tag.tag)}
          </span>
        ))}
      </div>
    </article>
  );
}

function DetailSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="detail-section">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

function TagsByImportance({ tags }: { tags: ProblemTag[] }) {
  return (
    <div className="tag-groups">
      {IMPORTANCE_VALUES.map((importance) => {
        const group = byImportance(tags, importance);
        if (!group.length) return null;
        return (
          <div key={importance} className="tag-group">
            <h4>{importance}</h4>
            {group.map((tag) => (
              <div key={`${tag.tag}:${tag.source}:${tag.importance}`} className="tag-evidence">
                <div>
                  <strong>{tag.tag}</strong>
                  <span>{tag.source}</span>
                </div>
                {tag.evidence ? <p>{tag.evidence}</p> : null}
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
}

function DetailDrawer({
  detail,
  loading,
  saving,
  note,
  favorite,
  setNote,
  setFavorite,
  onSave,
  onClose
}: {
  detail: ProblemDetail | null;
  loading: boolean;
  saving: boolean;
  note: string;
  favorite: boolean;
  setNote: (value: string) => void;
  setFavorite: (value: boolean) => void;
  onSave: () => void;
  onClose: () => void;
}) {
  return (
    <aside className={`drawer ${detail || loading ? "open" : ""}`}>
      <div className="drawer-header">
        <div>
          <span className="eyebrow">{detail?.label ?? "Problem"}</span>
          <h2>{detail?.title ?? "Loading"}</h2>
        </div>
        <button className="icon-button" onClick={onClose}>
          <X size={18} />
        </button>
      </div>

      {loading ? (
        <div className="loading-panel">
          <Loader2 className="spin" size={22} />
        </div>
      ) : null}

      {detail ? (
        <div className="drawer-content">
          <div className="drawer-actions">
            <a href={detail.canonical_url} target="_blank" rel="noreferrer" className="small-link">
              Codeforces <ExternalLink size={14} />
            </a>
            <a href={detail.problemset_url} target="_blank" rel="noreferrer" className="small-link">
              Problemset <ExternalLink size={14} />
            </a>
          </div>

          <div className="fact-grid">
            <div>
              <span>Rating</span>
              <strong>{detail.rating ?? detail.rating_status}</strong>
            </div>
            <div>
              <span>Contest</span>
              <strong>{detail.contest_title}</strong>
            </div>
            <div>
              <span>Status</span>
              <strong>{detail.annotation.review_status}</strong>
            </div>
            <div>
              <span>Confidence</span>
              <strong>{detail.annotation.confidence}</strong>
            </div>
          </div>

          <DetailSection title="Personal">
            <label className="switch-row">
              <input
                type="checkbox"
                checked={favorite}
                onChange={() => setFavorite(!favorite)}
              />
              <span>Favorite</span>
            </label>
            <textarea
              value={note}
              onChange={(event) => setNote(event.target.value)}
              rows={4}
              placeholder="Note"
            />
            <button className="save-button" onClick={onSave} disabled={saving}>
              {saving ? <Loader2 className="spin" size={16} /> : <Save size={16} />}
              Save
            </button>
          </DetailSection>

          <DetailSection title="Annotation">
            <p>{detail.annotation.summary}</p>
            <dl className="detail-list">
              <dt>Constraints</dt>
              <dd>{detail.annotation.constraints}</dd>
              <dt>Core Idea</dt>
              <dd>{detail.annotation.core_idea}</dd>
              <dt>Complexity</dt>
              <dd>{detail.annotation.complexity}</dd>
            </dl>
            <div className="tricks">
              {detail.annotation.tricks.map((trick) => (
                <span key={trick}>{trick}</span>
              ))}
            </div>
          </DetailSection>

          <DetailSection title="Tags">
            <TagsByImportance tags={detail.tags} />
          </DetailSection>

          <DetailSection title="Solution Variants">
            {detail.solution_variants.map((variant) => (
              <div key={variant.variant_name} className="variant-card">
                <div>
                  <strong>{variant.variant_name}</strong>
                  {variant.is_primary ? <span>primary</span> : null}
                </div>
                <p>{variant.summary}</p>
                <small>{variant.complexity}</small>
              </div>
            ))}
          </DetailSection>

          <DetailSection title="Sources">
            <div className="source-list">
              {detail.sources.map((source) => (
                <a key={`${source.source_type}:${source.url}`} href={source.url} target="_blank" rel="noreferrer">
                  <span>{source.source_type}</span>
                  <ExternalLink size={14} />
                </a>
              ))}
            </div>
          </DetailSection>

          {detail.aliases.length ? (
            <DetailSection title="Aliases">
              {detail.aliases.map((alias) => (
                <div key={alias.alias_problem_uid} className="alias-row">
                  {alias.alias_contest_id}
                  {alias.alias_problem_index}
                  <span>{alias.reason}</span>
                </div>
              ))}
            </DetailSection>
          ) : null}
        </div>
      ) : null}
    </aside>
  );
}

export function App() {
  const [tagTree, setTagTree] = useState<TagNode[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [results, setResults] = useState<SearchProblem[]>([]);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState<Set<string>>(
    new Set(["algorithm", "data-structure", "math", "paradigm", "trick"])
  );
  const [params, setParams] = useState<SearchParams>({
    ratingMin: "",
    ratingMax: "",
    ratingStatuses: ["official"],
    importance: ["primary", "secondary"],
    tags: [],
    tagMode: "and",
    favoriteOnly: false,
    query: ""
  });
  const [detail, setDetail] = useState<ProblemDetail | null>(null);
  const [note, setNote] = useState("");
  const [favorite, setFavorite] = useState(false);

  useEffect(() => {
    Promise.all([fetchTags(), fetchStats()])
      .then(([tags, nextStats]) => {
        setTagTree(tags);
        setStats(nextStats);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLoading(true);
      fetchSearch(params)
        .then((response) => {
          setResults(response.items);
          setError("");
        })
        .catch((err: Error) => setError(err.message))
        .finally(() => setLoading(false));
    }, 180);
    return () => window.clearTimeout(timer);
  }, [params]);

  const summary = useMemo(() => {
    if (!stats) return "Loading";
    return `${stats.canonical_problems} problems / ${stats.tags} tags / ${stats.favorites} favorites`;
  }, [stats]);

  const openDetail = (problemUid: string) => {
    setDetail(null);
    setDetailLoading(true);
    fetchProblem(problemUid)
      .then((item) => {
        setDetail(item);
        setFavorite(item.user_state.favorite);
        setNote(item.user_state.note);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setDetailLoading(false));
  };

  const saveDetailState = () => {
    if (!detail) return;
    setSaving(true);
    saveUserState(detail.problem_uid, favorite, note)
      .then((state) => {
        setDetail({
          ...detail,
          user_state: state
        });
        return fetchStats();
      })
      .then(setStats)
      .then(() => fetchSearch(params))
      .then((response) => setResults(response.items))
      .catch((err: Error) => setError(err.message))
      .finally(() => setSaving(false));
  };

  return (
    <div className="app-shell">
      <FilterPanel
        tagTree={tagTree}
        params={params}
        expanded={expanded}
        setParams={setParams}
        setExpanded={setExpanded}
      />
      <main className="content">
        <header className="topbar">
          <div>
            <h1>Codeforces DB</h1>
            <p>{summary}</p>
          </div>
          <div className="topbar-status">
            {loading ? <Loader2 className="spin" size={18} /> : null}
            <span>{results.length} shown</span>
          </div>
        </header>

        {error ? <div className="error-banner">{error}</div> : null}

        <section className="results">
          {results.map((problem) => (
            <ProblemResult key={problem.problem_uid} problem={problem} onOpen={openDetail} />
          ))}
          {!loading && !results.length ? (
            <div className="empty-state">No matching problems.</div>
          ) : null}
        </section>
      </main>

      <DetailDrawer
        detail={detail}
        loading={detailLoading}
        saving={saving}
        note={note}
        favorite={favorite}
        setNote={setNote}
        setFavorite={setFavorite}
        onSave={saveDetailState}
        onClose={() => setDetail(null)}
      />
    </div>
  );
}
