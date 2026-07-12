import * as Collapsible from "@radix-ui/react-collapsible";
import { Ban, ChevronRight, RotateCcw, Search, SlidersHorizontal } from "lucide-react";
import { useState } from "react";
import { importanceLabel, ratingStatusLabel, tagLabel } from "../../i18n";
import type {
  FavoriteFilter,
  Importance,
  Locale,
  Priority,
  ProgressStatus,
  RatingStatus,
  SearchFacets,
  SearchParams,
  TagNode
} from "../../types";
import { toggleValue } from "../../shared/urlState";
import { CheckControl } from "../../shared/ui";

const PROGRESS: ProgressStatus[] = ["unattempted", "attempted", "solved"];
const PRIORITIES: Array<Priority | "unassigned"> = ["critical", "high", "normal", "low", "unassigned"];
const RATING_STATUSES: RatingStatus[] = ["official", "pending_cf_rating", "no_cf_rating", "unknown"];
const IMPORTANCE: Importance[] = ["primary", "secondary", "incidental"];

const text = (locale: Locale, zh: string, en: string) => locale === "zh" ? zh : en;
const progressText = (locale: Locale, value: ProgressStatus) => ({
  unattempted: text(locale, "未尝试", "Unattempted"),
  attempted: text(locale, "尝试过", "Attempted"),
  solved: text(locale, "已解决", "Solved")
})[value];
const priorityText = (locale: Locale, value: Priority | "unassigned") => ({
  critical: text(locale, "非常重要", "Critical"),
  high: text(locale, "重要", "High"),
  normal: text(locale, "一般", "Normal"),
  low: text(locale, "次要", "Low"),
  unassigned: text(locale, "未设置", "Unassigned")
})[value];

function TagTreeItem({
  node,
  locale,
  params,
  counts,
  expanded,
  setExpanded,
  onChange
}: {
  node: TagNode;
  locale: Locale;
  params: SearchParams;
  counts: Record<string, number>;
  expanded: Set<string>;
  setExpanded: (next: Set<string>) => void;
  onChange: (changes: Partial<SearchParams>) => void;
}) {
  const open = expanded.has(node.tag);
  const included = params.tags.includes(node.tag);
  const excluded = params.excludeTags.includes(node.tag);
  const toggleOpen = () => {
    const next = new Set(expanded);
    if (open) next.delete(node.tag); else next.add(node.tag);
    setExpanded(next);
  };
  const toggleIncluded = () => onChange({
    tags: toggleValue(params.tags, node.tag),
    excludeTags: params.excludeTags.filter((tag) => tag !== node.tag)
  });
  const toggleExcluded = () => onChange({
    excludeTags: toggleValue(params.excludeTags, node.tag),
    tags: params.tags.filter((tag) => tag !== node.tag)
  });

  return (
    <Collapsible.Root className="tag-node" open={open} onOpenChange={toggleOpen}>
      <div className={`tag-row ${included ? "included" : ""} ${excluded ? "excluded" : ""}`}>
        {node.children.length ? (
          <Collapsible.Trigger className="tree-trigger" aria-label={text(locale, "展开标签", "Expand tag")}>
            <ChevronRight className={open ? "rotated" : ""} size={14} />
          </Collapsible.Trigger>
        ) : <span className="tree-spacer" />}
        <button className="tag-select" type="button" onClick={toggleIncluded} title={node.tag}>
          <span className="tag-dot" />
          <span>{tagLabel(locale, node.tag)}</span>
        </button>
        <span className="facet-count">{counts[node.tag] ?? node.problem_count}</span>
        <button
          type="button"
          className={`exclude-button ${excluded ? "active" : ""}`}
          onClick={toggleExcluded}
          aria-label={text(locale, `排除 ${node.tag}`, `Exclude ${node.tag}`)}
        ><Ban size={12} /></button>
      </div>
      <Collapsible.Content className="tag-children">
        {node.children.map((child) => (
          <TagTreeItem
            key={child.tag}
            node={child}
            locale={locale}
            params={params}
            counts={counts}
            expanded={expanded}
            setExpanded={setExpanded}
            onChange={onChange}
          />
        ))}
      </Collapsible.Content>
    </Collapsible.Root>
  );
}

export function FilterSidebar({
  tagTree,
  facets,
  params,
  locale,
  onChange,
  onReset
}: {
  tagTree: TagNode[];
  facets?: SearchFacets;
  params: SearchParams;
  locale: Locale;
  onChange: (changes: Partial<SearchParams>) => void;
  onReset: () => void;
}) {
  const [expanded, setExpanded] = useState<Set<string>>(
    new Set(["algorithm", "data-structure", "dp", "graph", "math", "string"])
  );
  const favoriteOptions: FavoriteFilter[] = ["any", "favorite", "not_favorite"];

  return (
    <aside className="filter-sidebar" aria-label={text(locale, "题目筛选", "Problem filters")}>
      <header className="sidebar-header">
        <div><Search size={17} /><strong>{text(locale, "筛选", "Filters")}</strong></div>
        <button type="button" className="text-button" onClick={onReset}>
          <RotateCcw size={14} /> {text(locale, "重置", "Reset")}
        </button>
      </header>

      <label className="field">
        <span>{text(locale, "搜索", "Search")}</span>
        <div className="input-with-icon">
          <input
            value={params.query}
            onChange={(event) => onChange({ query: event.target.value })}
            placeholder={text(locale, "题目标题 / 编号 / 标签", "Title / ID / tag")}
          />
          <Search size={15} />
        </div>
      </label>

      <section className="filter-section">
        <h2>{text(locale, "Rating 范围", "Rating range")}</h2>
        <div className="rating-inputs">
          <input inputMode="numeric" value={params.ratingMin} placeholder="800" onChange={(event) => onChange({ ratingMin: event.target.value })} />
          <span>—</span>
          <input inputMode="numeric" value={params.ratingMax} placeholder="3500" onChange={(event) => onChange({ ratingMax: event.target.value })} />
        </div>
      </section>

      <section className="filter-section">
        <h2>{text(locale, "收藏", "Favorites")}</h2>
        <div className="segmented three">
          {favoriteOptions.map((value) => (
            <button key={value} type="button" className={params.favorite === value ? "active" : ""} onClick={() => onChange({ favorite: value })}>
              {value === "any" ? text(locale, "全部", "All") : value === "favorite" ? text(locale, "已收藏", "Saved") : text(locale, "未收藏", "Unsaved")}
              <small>{facets?.favorite[value === "any" ? "all" : value] ?? 0}</small>
            </button>
          ))}
        </div>
      </section>

      <section className="filter-section">
        <h2>{text(locale, "状态", "Progress")}</h2>
        {PROGRESS.map((value) => (
          <CheckControl
            key={value}
            checked={params.progressStatuses.includes(value)}
            onChange={() => onChange({ progressStatuses: toggleValue(params.progressStatuses, value) })}
            label={<><span>{progressText(locale, value)}</span><small>{facets?.progress[value] ?? 0}</small></>}
          />
        ))}
      </section>

      <section className="filter-section priority-filter">
        <h2>{text(locale, "重要性", "Priority")}</h2>
        {PRIORITIES.map((value) => (
          <CheckControl
            key={value}
            checked={params.priorities.includes(value)}
            onChange={() => onChange({ priorities: toggleValue(params.priorities, value) })}
            label={<><span className={`priority-label priority-${value}`}><i />{priorityText(locale, value)}</span><small>{facets?.priority[value] ?? 0}</small></>}
          />
        ))}
      </section>

      <section className="filter-section tag-filter">
        <h2>{text(locale, "标签", "Tags")}</h2>
        {(params.tags.length || params.excludeTags.length) ? (
          <div className="selected-tags">
            {params.tags.map((tag) => <button key={tag} onClick={() => onChange({ tags: params.tags.filter((item) => item !== tag) })}>+ {tagLabel(locale, tag, "path")}</button>)}
            {params.excludeTags.map((tag) => <button className="excluded" key={tag} onClick={() => onChange({ excludeTags: params.excludeTags.filter((item) => item !== tag) })}>− {tagLabel(locale, tag, "path")}</button>)}
          </div>
        ) : null}
        <div className="tag-tree">
          {tagTree.map((node) => (
            <TagTreeItem key={node.tag} node={node} locale={locale} params={params} counts={facets?.tag_counts ?? {}} expanded={expanded} setExpanded={setExpanded} onChange={onChange} />
          ))}
        </div>
      </section>

      <Collapsible.Root className="advanced-filter">
        <Collapsible.Trigger className="advanced-trigger">
          <SlidersHorizontal size={15} /> {text(locale, "高级筛选", "Advanced filters")} <ChevronRight size={14} />
        </Collapsible.Trigger>
        <Collapsible.Content className="advanced-content">
          <div className="segmented">
            {(["and", "or"] as const).map((mode) => <button key={mode} type="button" className={params.tagMode === mode ? "active" : ""} onClick={() => onChange({ tagMode: mode })}>{mode.toUpperCase()}</button>)}
          </div>
          <h3>{text(locale, "标签主次", "Tag importance")}</h3>
          {IMPORTANCE.map((value) => <CheckControl key={value} checked={params.importance.includes(value)} onChange={() => onChange({ importance: toggleValue(params.importance, value) })} label={importanceLabel(locale, value)} />)}
          <h3>{text(locale, "Rating 状态", "Rating status")}</h3>
          {RATING_STATUSES.map((value) => <CheckControl key={value} checked={params.ratingStatuses.includes(value)} onChange={() => onChange({ ratingStatuses: toggleValue(params.ratingStatuses, value) })} label={ratingStatusLabel(locale, value)} />)}
        </Collapsible.Content>
      </Collapsible.Root>
    </aside>
  );
}
