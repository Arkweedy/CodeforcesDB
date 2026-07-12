import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BarChart3, Database, Menu, RefreshCw, Settings as SettingsIcon } from "lucide-react";
import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { readStoredLocale, writeStoredLocale } from "../i18n";
import type { Locale, ProgressStatus, SearchParams, SearchResponse, Settings, UserState } from "../types";
import { FilterSidebar } from "../features/filters/FilterSidebar";
import { ProblemDetail } from "../features/problems/ProblemDetail";
import { ProblemList } from "../features/problems/ProblemList";
import { IconButton, Modal } from "../shared/ui";
import { DEFAULT_SEARCH, readUrlState, writeUrlState } from "../shared/urlState";

const text = (locale: Locale, zh: string, en: string) => locale === "zh" ? zh : en;
const AnalyticsDialog = lazy(() => import("../features/analytics/AnalyticsDialog").then((module) => ({ default: module.AnalyticsDialog })));
const SettingsDialog = lazy(() => import("../features/settings/SettingsDialog").then((module) => ({ default: module.SettingsDialog })));

function optimisticState(problem: SearchResponse["items"][number], changes: Partial<UserState>) {
  const manual: ProgressStatus | null = Object.prototype.hasOwnProperty.call(changes, "manual_progress")
    ? changes.manual_progress ?? null
    : problem.manual_progress;
  return {
    ...problem,
    ...changes,
    manual_progress: manual,
    progress_status: manual ?? problem.synced_progress ?? "unattempted"
  };
}

export function App() {
  const queryClient = useQueryClient();
  const [params, setParams] = useState<SearchParams>(() => readUrlState());
  const [locale, setLocale] = useState<Locale>(() => readStoredLocale());
  const [analyticsOpen, setAnalyticsOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [detailDirty, setDetailDirty] = useState(false);
  const [mutationError, setMutationError] = useState("");

  const settingsQuery = useQuery({ queryKey: ["settings"], queryFn: ({ signal }) => api.settings(signal) });
  const tagsQuery = useQuery({ queryKey: ["tags"], queryFn: ({ signal }) => api.tags(signal) });
  const searchQuery = useQuery({
    queryKey: ["search", params],
    queryFn: ({ signal }) => api.search(params, signal),
    placeholderData: (previous) => previous
  });

  useEffect(() => writeUrlState(params), [params]);
  useEffect(() => {
    const onPopState = () => setParams(readUrlState());
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);
  useEffect(() => {
    const settings = settingsQuery.data;
    if (!settings) return;
    setLocale(settings.locale);
    writeStoredLocale(settings.locale);
    document.documentElement.dataset.density = settings.density;
  }, [settingsQuery.data]);

  const changeParams = useCallback((changes: Partial<SearchParams>) => {
    setParams((current) => {
      const onlyNavigation = Object.keys(changes).every((key) => key === "page" || key === "problemUid");
      return { ...current, ...changes, page: onlyNavigation ? (changes.page ?? current.page) : 1 };
    });
  }, []);
  const reset = () => setParams({ ...DEFAULT_SEARCH, pageSize: params.pageSize, problemUid: params.problemUid });

  const userMutation = useMutation({
    mutationFn: ({ problemUid, changes }: { problemUid: string; changes: Partial<Pick<UserState, "favorite" | "note" | "manual_progress" | "priority">> }) => api.patchUserState(problemUid, changes),
    onMutate: async ({ problemUid, changes }) => {
      setMutationError("");
      await queryClient.cancelQueries({ queryKey: ["search"] });
      await queryClient.cancelQueries({ queryKey: ["problem", problemUid] });
      const searches = queryClient.getQueriesData<SearchResponse>({ queryKey: ["search"] });
      const detail = queryClient.getQueryData(["problem", problemUid]);
      searches.forEach(([key, data]) => {
        if (!data) return;
        queryClient.setQueryData<SearchResponse>(key, {
          ...data,
          items: data.items.map((problem) => problem.problem_uid === problemUid ? optimisticState(problem, changes) : problem)
        });
      });
      queryClient.setQueryData(["problem", problemUid], (current: any) => {
        if (!current) return current;
        const manual = Object.prototype.hasOwnProperty.call(changes, "manual_progress")
          ? changes.manual_progress ?? null
          : current.user_state.manual_progress;
        return {
          ...current,
          user_state: { ...current.user_state, ...changes, manual_progress: manual, progress_status: manual ?? current.user_state.synced_progress ?? "unattempted" }
        };
      });
      return { searches, detail };
    },
    onError: (error, variables, context) => {
      context?.searches.forEach(([key, data]) => queryClient.setQueryData(key, data));
      queryClient.setQueryData(["problem", variables.problemUid], context?.detail);
      setMutationError((error as Error).message);
    },
    onSuccess: (state, { problemUid }) => {
      queryClient.setQueryData(["problem", problemUid], (current: any) => current ? { ...current, user_state: state } : current);
    },
    onSettled: (_data, _error, variables) => {
      queryClient.invalidateQueries({ queryKey: ["search"] });
      queryClient.invalidateQueries({ queryKey: ["problem", variables.problemUid] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    }
  });

  const patchState = (problemUid: string, changes: Partial<Pick<UserState, "favorite" | "note" | "manual_progress" | "priority">>) => userMutation.mutateAsync({ problemUid, changes });
  const openProblem = (problemUid: string) => {
    if (detailDirty && params.problemUid !== problemUid && !window.confirm(text(locale, "备注尚未保存，放弃修改并打开另一题吗？", "Discard the note and open another problem?"))) return;
    changeParams({ problemUid });
  };
  const closeProblem = () => changeParams({ problemUid: null });
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["search"] });
    queryClient.invalidateQueries({ queryKey: ["tags"] });
    if (params.problemUid) queryClient.invalidateQueries({ queryKey: ["problem", params.problemUid] });
  };
  const applySettings = (settings: Settings) => {
    setLocale(settings.locale);
    writeStoredLocale(settings.locale);
    document.documentElement.dataset.density = settings.density;
    changeParams({ pageSize: settings.page_size });
  };

  const error = mutationError || (searchQuery.error as Error | null)?.message || (tagsQuery.error as Error | null)?.message;
  const filters = <FilterSidebar tagTree={tagsQuery.data ?? []} facets={searchQuery.data?.facets} params={params} locale={locale} onChange={changeParams} onReset={reset} />;

  return (
    <div className={`app-layout ${params.problemUid ? "has-detail" : ""}`}>
      <div className="desktop-filters">{filters}</div>
      <main className="workspace">
        <header className="app-topbar">
          <div className="brand">
            <button className="mobile-filter-button" onClick={() => setFiltersOpen(true)} aria-label={text(locale, "打开筛选", "Open filters")}><Menu size={19} /></button>
            <Database size={22} />
            <div><h1>Codeforces {text(locale, "题库", "DB")}</h1><p>{text(locale, "AI-reviewed 本地训练题库", "AI-reviewed local training database")}</p></div>
          </div>
          <div className="topbar-actions">
            <IconButton label={text(locale, "刷新本地数据", "Refresh local data")} onClick={refresh}><RefreshCw size={18} /></IconButton>
            <IconButton label={text(locale, "题库分析", "Analytics")} onClick={() => setAnalyticsOpen(true)}><BarChart3 size={18} /></IconButton>
            <IconButton label={text(locale, "设置", "Settings")} onClick={() => setSettingsOpen(true)}><SettingsIcon size={18} /></IconButton>
          </div>
        </header>
        {error ? <div className="error-banner app-error">{error}<button onClick={() => setMutationError("")}>×</button></div> : null}
        <ProblemList
          data={searchQuery.data}
          params={params}
          locale={locale}
          loading={searchQuery.isFetching}
          selectedUid={params.problemUid}
          onChangeParams={changeParams}
          onOpen={openProblem}
          onPatch={(problemUid, changes) => { void patchState(problemUid, changes); }}
        />
      </main>

      <ProblemDetail problemUid={params.problemUid} locale={locale} onClose={closeProblem} onDirtyChange={setDetailDirty} onPatch={patchState} />
      <Suspense fallback={null}>
        {analyticsOpen ? <AnalyticsDialog open={analyticsOpen} onOpenChange={setAnalyticsOpen} params={params} locale={locale} /> : null}
        {settingsOpen ? <SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} locale={locale} onApplied={applySettings} /> : null}
      </Suspense>
      <Modal open={filtersOpen} onOpenChange={setFiltersOpen} title={text(locale, "筛选", "Filters")} description={text(locale, "缩小题目范围", "Narrow the problem set")} className="filter-modal">{filters}</Modal>
    </div>
  );
}
