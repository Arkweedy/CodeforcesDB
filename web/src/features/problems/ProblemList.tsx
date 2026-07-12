import * as Popover from "@radix-ui/react-popover";
import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Circle,
  Clock3,
  Flag,
  Loader2,
  Star
} from "lucide-react";
import { ratingText, tagLabel } from "../../i18n";
import { ratingClassName } from "../../colors";
import type {
  Locale,
  Priority,
  ProgressStatus,
  SearchParams,
  SearchProblem,
  SearchResponse,
  SortBy,
  SortOrder,
  UserState
} from "../../types";
import { SelectControl } from "../../shared/ui";

const text = (locale: Locale, zh: string, en: string) => locale === "zh" ? zh : en;

export const progressLabel = (locale: Locale, value: ProgressStatus) => ({
  unattempted: text(locale, "未尝试", "Unattempted"),
  attempted: text(locale, "尝试过", "Attempted"),
  solved: text(locale, "已解决", "Solved")
})[value];

export const priorityLabel = (locale: Locale, value: Priority | null) => value ? ({
  critical: text(locale, "非常重要", "Critical"),
  high: text(locale, "重要", "High"),
  normal: text(locale, "一般", "Normal"),
  low: text(locale, "次要", "Low")
})[value] : text(locale, "未设置", "Unassigned");

function ProgressIcon({ value }: { value: ProgressStatus }) {
  if (value === "solved") return <CheckCircle2 size={16} />;
  if (value === "attempted") return <Clock3 size={16} />;
  return <Circle size={16} />;
}

function ChoicePopover<T extends string | null>({
  value,
  values,
  label,
  className,
  renderValue,
  onChange
}: {
  value: T;
  values: T[];
  label: string;
  className: string;
  renderValue: (value: T) => React.ReactNode;
  onChange: (value: T) => void;
}) {
  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button className={className} type="button" aria-label={label}>{renderValue(value)}</button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content className="choice-popover" sideOffset={6} align="end">
          {values.map((option, index) => (
            <Popover.Close asChild key={option ?? `null-${index}`}>
              <button className={option === value ? "active" : ""} type="button" onClick={() => onChange(option)}>{renderValue(option)}</button>
            </Popover.Close>
          ))}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}

function ProblemRow({
  problem,
  locale,
  selected,
  onOpen,
  onPatch
}: {
  problem: SearchProblem;
  locale: Locale;
  selected: boolean;
  onOpen: () => void;
  onPatch: (changes: Partial<Pick<UserState, "favorite" | "manual_progress" | "priority">>) => void;
}) {
  const tags = [...new Map(problem.tags.filter((tag) => tag.importance !== "incidental").map((tag) => [tag.tag, tag])).values()].slice(0, 3);
  const stop = (event: React.MouseEvent) => event.stopPropagation();
  return (
    <tr className={selected ? "selected" : ""} onClick={onOpen} tabIndex={0} onKeyDown={(event) => { if (event.key === "Enter") onOpen(); }}>
      <td className="problem-id">{problem.label}</td>
      <td><button className="problem-title" type="button" onClick={onOpen}>{problem.title}</button></td>
      <td><span className={ratingClassName(problem.rating, problem.rating_status)}>{ratingText(locale, problem.rating, problem.rating_status)}</span></td>
      <td><div className="row-tags">{tags.map((tag) => <span key={tag.tag} title={tag.tag}>{tagLabel(locale, tag.tag)}</span>)}</div></td>
      <td onClick={stop}>
        <ChoicePopover
          value={problem.progress_status}
          values={["unattempted", "attempted", "solved"]}
          label={text(locale, "修改状态", "Change progress")}
          className={`progress-button progress-${problem.progress_status}`}
          renderValue={(value) => <><ProgressIcon value={value} /><span>{progressLabel(locale, value)}</span></>}
          onChange={(manual_progress) => onPatch({ manual_progress })}
        />
      </td>
      <td onClick={stop}>
        <ChoicePopover
          value={problem.priority}
          values={["critical", "high", "normal", "low", null]}
          label={text(locale, "修改重要性", "Change priority")}
          className={`priority-button priority-${problem.priority ?? "unassigned"}`}
          renderValue={(value) => <><Flag size={16} fill={value ? "currentColor" : "none"} /><span>{priorityLabel(locale, value)}</span></>}
          onChange={(priority) => onPatch({ priority })}
        />
      </td>
      <td onClick={stop}>
        <button className={`favorite-button ${problem.favorite ? "active" : ""}`} type="button" aria-label={text(locale, "切换收藏", "Toggle favorite")} onClick={() => onPatch({ favorite: !problem.favorite })}>
          <Star size={17} fill={problem.favorite ? "currentColor" : "none"} />
        </button>
      </td>
    </tr>
  );
}

function ProblemCard({ problem, locale, onOpen, onPatch }: {
  problem: SearchProblem;
  locale: Locale;
  onOpen: () => void;
  onPatch: (changes: Partial<Pick<UserState, "favorite" | "manual_progress" | "priority">>) => void;
}) {
  return (
    <article className="problem-card" onClick={onOpen}>
      <header><span>{problem.label}</span><button className={`favorite-button ${problem.favorite ? "active" : ""}`} onClick={(event) => { event.stopPropagation(); onPatch({ favorite: !problem.favorite }); }}><Star size={17} fill={problem.favorite ? "currentColor" : "none"} /></button></header>
      <h3>{problem.title}</h3>
      <div className="card-meta">
        <span className={ratingClassName(problem.rating, problem.rating_status)}>{ratingText(locale, problem.rating, problem.rating_status)}</span>
        <span className={`progress-pill progress-${problem.progress_status}`}><ProgressIcon value={problem.progress_status} />{progressLabel(locale, problem.progress_status)}</span>
        <span className={`priority-pill priority-${problem.priority ?? "unassigned"}`}><Flag size={14} />{priorityLabel(locale, problem.priority)}</span>
      </div>
      <div className="row-tags">{problem.tags.slice(0, 4).map((tag) => <span key={`${tag.tag}:${tag.importance}`}>{tagLabel(locale, tag.tag)}</span>)}</div>
    </article>
  );
}

function Pagination({ total, params, locale, onChange }: { total: number; params: SearchParams; locale: Locale; onChange: (page: number) => void }) {
  const pages = Math.max(1, Math.ceil(total / params.pageSize));
  const start = Math.max(1, Math.min(params.page - 2, pages - 4));
  const visible = Array.from({ length: Math.min(5, pages) }, (_, index) => start + index);
  return (
    <footer className="pagination">
      <span>{text(locale, `共 ${total} 题`, `${total} problems`)}</span>
      <div>
        <button disabled={params.page <= 1} onClick={() => onChange(params.page - 1)}><ChevronLeft size={16} /></button>
        {visible.map((page) => <button key={page} className={page === params.page ? "active" : ""} onClick={() => onChange(page)}>{page}</button>)}
        <button disabled={params.page >= pages} onClick={() => onChange(params.page + 1)}><ChevronRight size={16} /></button>
      </div>
      <span>{text(locale, `第 ${params.page} / ${pages} 页`, `Page ${params.page} / ${pages}`)}</span>
    </footer>
  );
}

export function ProblemList({
  data,
  params,
  locale,
  loading,
  selectedUid,
  onChangeParams,
  onOpen,
  onPatch
}: {
  data?: SearchResponse;
  params: SearchParams;
  locale: Locale;
  loading: boolean;
  selectedUid: string | null;
  onChangeParams: (changes: Partial<SearchParams>) => void;
  onOpen: (problemUid: string) => void;
  onPatch: (problemUid: string, changes: Partial<Pick<UserState, "favorite" | "manual_progress" | "priority">>) => void;
}) {
  const summary = data?.summary;
  const stats = [
    [text(locale, "题目总数", "Total"), summary?.total ?? 0],
    [text(locale, "已解决", "Solved"), summary?.solved ?? 0],
    [text(locale, "尝试过", "Attempted"), summary?.attempted ?? 0],
    [text(locale, "未尝试", "Unattempted"), summary?.unattempted ?? 0],
    [text(locale, "收藏数", "Favorites"), summary?.favorites ?? 0],
    [text(locale, "最高 Rating", "Max rating"), summary?.max_rating ?? "—"]
  ];
  return (
    <>
      <section className="stats-strip" aria-label={text(locale, "筛选结果统计", "Result summary")}>
        {stats.map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}
      </section>
      <section className="list-toolbar">
        <div><strong>{text(locale, "题目列表", "Problem list")}</strong>{loading ? <Loader2 className="spin" size={16} /> : null}</div>
        <div>
          <SelectControl<SortBy>
            label={text(locale, "排序字段", "Sort field")}
            value={params.sortBy}
            onChange={(sortBy) => onChangeParams({ sortBy })}
            options={[
              { value: "rating", label: "Rating" },
              { value: "problem", label: text(locale, "题号", "Problem") },
              { value: "title", label: text(locale, "标题", "Title") },
              { value: "progress", label: text(locale, "状态", "Progress") },
              { value: "priority", label: text(locale, "重要性", "Priority") },
              { value: "favorite", label: text(locale, "收藏", "Favorite") }
            ]}
          />
          <SelectControl<SortOrder>
            label={text(locale, "排序方向", "Sort order")}
            value={params.sortOrder}
            onChange={(sortOrder) => onChangeParams({ sortOrder })}
            options={[{ value: "asc", label: text(locale, "升序", "Ascending") }, { value: "desc", label: text(locale, "降序", "Descending") }]}
          />
        </div>
      </section>
      <section className="problem-list-wrap">
        <table className="problem-table">
          <thead><tr><th>#</th><th>{text(locale, "题目", "Problem")}</th><th>Rating</th><th>{text(locale, "标签", "Tags")}</th><th>{text(locale, "状态", "Progress")}</th><th>{text(locale, "重要性", "Priority")}</th><th>{text(locale, "收藏", "Favorite")}</th></tr></thead>
          <tbody>{data?.items.map((problem) => <ProblemRow key={problem.problem_uid} problem={problem} locale={locale} selected={problem.problem_uid === selectedUid} onOpen={() => onOpen(problem.problem_uid)} onPatch={(changes) => onPatch(problem.problem_uid, changes)} />)}</tbody>
        </table>
        <div className="problem-cards">{data?.items.map((problem) => <ProblemCard key={problem.problem_uid} problem={problem} locale={locale} onOpen={() => onOpen(problem.problem_uid)} onPatch={(changes) => onPatch(problem.problem_uid, changes)} />)}</div>
        {!loading && !data?.items.length ? <div className="empty-state">{text(locale, "没有符合条件的题目", "No matching problems")}</div> : null}
      </section>
      <Pagination total={data?.total ?? 0} params={params} locale={locale} onChange={(page) => onChangeParams({ page })} />
    </>
  );
}
