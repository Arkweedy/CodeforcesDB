import * as Dialog from "@radix-ui/react-dialog";
import { useQuery } from "@tanstack/react-query";
import { ExternalLink, Loader2, Pencil, Save, Star, X } from "lucide-react";
import { useEffect, useState } from "react";
import { ratingClassName } from "../../colors";
import { importanceLabel, ratingText, tagLabel, valueLabel } from "../../i18n";
import { api } from "../../api";
import type { Locale, Priority, ProgressStatus, UserState } from "../../types";
import { IconButton, SelectControl } from "../../shared/ui";
import { priorityLabel, progressLabel } from "./ProblemList";

const text = (locale: Locale, zh: string, en: string) => locale === "zh" ? zh : en;

function useDesktop(): boolean {
  const [desktop, setDesktop] = useState(() => window.matchMedia("(min-width: 1200px)").matches);
  useEffect(() => {
    const media = window.matchMedia("(min-width: 1200px)");
    const listener = () => setDesktop(media.matches);
    media.addEventListener("change", listener);
    return () => media.removeEventListener("change", listener);
  }, []);
  return desktop;
}

export function ProblemDetail({
  problemUid,
  locale,
  onClose,
  onDirtyChange,
  onPatch
}: {
  problemUid: string | null;
  locale: Locale;
  onClose: () => void;
  onDirtyChange: (dirty: boolean) => void;
  onPatch: (problemUid: string, changes: Partial<Pick<UserState, "favorite" | "note" | "manual_progress" | "priority">>) => Promise<UserState>;
}) {
  const desktop = useDesktop();
  const { data: detail, isLoading, error } = useQuery({
    queryKey: ["problem", problemUid],
    queryFn: ({ signal }) => api.problem(problemUid!, signal),
    enabled: Boolean(problemUid)
  });
  const [editingNote, setEditingNote] = useState(false);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setNote(detail?.user_state.note ?? "");
    setEditingNote(false);
    onDirtyChange(false);
  }, [detail?.problem_uid]);

  const dirty = Boolean(detail && note !== detail.user_state.note);
  useEffect(() => onDirtyChange(dirty), [dirty, onDirtyChange]);

  const requestClose = () => {
    if (dirty && !window.confirm(text(locale, "备注尚未保存，确定关闭吗？", "Discard the unsaved note?"))) return;
    onClose();
  };
  const saveNote = async () => {
    if (!detail) return;
    setSaving(true);
    try {
      await onPatch(detail.problem_uid, { note });
      setEditingNote(false);
    } finally {
      setSaving(false);
    }
  };

  const content = (
    <>
          <header className="detail-header">
            <div>
              <span>{detail?.label ?? "Codeforces"}</span>
              {desktop ? <h2>{detail?.title ?? text(locale, "加载中", "Loading")}</h2> : <Dialog.Title>{detail?.title ?? text(locale, "加载中", "Loading")}</Dialog.Title>}
              {desktop ? <p>{detail?.contest_title ?? text(locale, "题目详情", "Problem details")}</p> : <Dialog.Description>{detail?.contest_title ?? text(locale, "题目详情", "Problem details")}</Dialog.Description>}
            </div>
            <IconButton label={text(locale, "关闭", "Close")} onClick={requestClose}><X size={18} /></IconButton>
          </header>
          {isLoading ? <div className="detail-loading"><Loader2 className="spin" /></div> : null}
          {error ? <div className="error-banner">{(error as Error).message}</div> : null}
          {detail ? (
            <div className="detail-body">
              <div className="detail-actions">
                <span className={ratingClassName(detail.rating, detail.rating_status)}>{ratingText(locale, detail.rating, detail.rating_status)}</span>
                <IconButton label={text(locale, detail.user_state.favorite ? "取消收藏" : "收藏", detail.user_state.favorite ? "Unfavorite" : "Favorite")} onClick={() => onPatch(detail.problem_uid, { favorite: !detail.user_state.favorite })} className={detail.user_state.favorite ? "favorite-active" : ""}><Star size={18} fill={detail.user_state.favorite ? "currentColor" : "none"} /></IconButton>
                <a className="external-link" href={detail.canonical_url} target="_blank" rel="noreferrer">Codeforces <ExternalLink size={14} /></a>
              </div>

              <section className="detail-controls">
                <label><span>{text(locale, "做题状态", "Progress")}</span><SelectControl<ProgressStatus | "synced"> label={text(locale, "做题状态", "Progress")} value={detail.user_state.manual_progress ?? "synced"} onChange={(value) => onPatch(detail.problem_uid, { manual_progress: value === "synced" ? null : value })} options={[
                  { value: "synced", label: text(locale, `跟随同步（${progressLabel(locale, detail.user_state.synced_progress ?? "unattempted")}）`, `Synced (${progressLabel(locale, detail.user_state.synced_progress ?? "unattempted")})`) },
                  { value: "unattempted", label: progressLabel(locale, "unattempted") },
                  { value: "attempted", label: progressLabel(locale, "attempted") },
                  { value: "solved", label: progressLabel(locale, "solved") }
                ]} /></label>
                <label><span>{text(locale, "重要性", "Priority")}</span><SelectControl<Priority | "unassigned"> label={text(locale, "重要性", "Priority")} value={detail.user_state.priority ?? "unassigned"} onChange={(value) => onPatch(detail.problem_uid, { priority: value === "unassigned" ? null : value })} options={[
                  { value: "critical", label: priorityLabel(locale, "critical") },
                  { value: "high", label: priorityLabel(locale, "high") },
                  { value: "normal", label: priorityLabel(locale, "normal") },
                  { value: "low", label: priorityLabel(locale, "low") },
                  { value: "unassigned", label: priorityLabel(locale, null) }
                ]} /></label>
              </section>

              <section className="detail-section">
                <h3>{text(locale, "题目注释", "Annotation")}</h3>
                <p>{detail.annotation.summary || text(locale, "暂无注释", "No annotation")}</p>
                <dl>
                  <dt>{text(locale, "约束", "Constraints")}</dt><dd>{detail.annotation.constraints || "—"}</dd>
                  <dt>{text(locale, "核心思路", "Core idea")}</dt><dd>{detail.annotation.core_idea || "—"}</dd>
                  <dt>{text(locale, "复杂度", "Complexity")}</dt><dd>{detail.annotation.complexity || "—"}</dd>
                </dl>
              </section>

              <section className="detail-section">
                <h3>{text(locale, "标签依据", "Tag evidence")}</h3>
                <div className="evidence-list">{detail.tags.map((tag) => (
                  <article key={`${tag.tag}:${tag.importance}:${tag.source}`}>
                    <header><strong>{tagLabel(locale, tag.tag, "path")}</strong><span>{importanceLabel(locale, tag.importance)} · {valueLabel(locale, tag.source)}</span></header>
                    {tag.evidence ? <p>{tag.evidence}</p> : null}
                  </article>
                ))}</div>
              </section>

              <section className="detail-section">
                <h3>{text(locale, "解法变体", "Solution variants")}</h3>
                <div className="variant-list">{detail.solution_variants.map((variant) => (
                  <article key={variant.variant_name}><header><strong>{valueLabel(locale, variant.variant_name)}</strong>{variant.is_primary ? <span>{text(locale, "主要", "Primary")}</span> : null}</header><p>{variant.summary}</p><small>{variant.complexity}</small></article>
                ))}</div>
              </section>

              <section className="detail-section">
                <h3>{text(locale, "参考资料", "Sources")}</h3>
                <div className="source-list">{detail.sources.map((source) => (
                  <a key={`${source.source_type}:${source.url}`} href={source.url} target="_blank" rel="noreferrer"><span><strong>{valueLabel(locale, source.source_type)}</strong>{source.notes ? <small>{source.notes}</small> : null}</span><span>{source.fetched_at ? source.fetched_at.slice(0, 10) : ""}<ExternalLink size={14} /></span></a>
                ))}</div>
              </section>

              <section className="detail-section note-section">
                <header><h3>{text(locale, "我的笔记", "My note")}</h3>{!editingNote ? <IconButton label={text(locale, "编辑笔记", "Edit note")} onClick={() => setEditingNote(true)}><Pencil size={16} /></IconButton> : null}</header>
                {editingNote ? <><textarea rows={6} value={note} onChange={(event) => setNote(event.target.value)} autoFocus /><div className="note-actions"><button className="secondary-button" onClick={() => { setNote(detail.user_state.note); setEditingNote(false); }}>{text(locale, "取消", "Cancel")}</button><button className="primary-button" onClick={saveNote} disabled={saving}>{saving ? <Loader2 className="spin" size={15} /> : <Save size={15} />}{text(locale, "保存", "Save")}</button></div></> : <p className="note-card">{detail.user_state.note || text(locale, "暂无笔记", "No note yet")}</p>}
              </section>
            </div>
          ) : null}
    </>
  );

  if (desktop) {
    return problemUid ? <aside className="detail-panel" aria-label={text(locale, "题目详情", "Problem details")}>{content}</aside> : null;
  }

  return (
    <Dialog.Root open={Boolean(problemUid)} modal onOpenChange={(open) => { if (!open) requestClose(); }}>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay detail-overlay" />
        <Dialog.Content className="detail-panel" onEscapeKeyDown={(event) => { if (dirty) { event.preventDefault(); requestClose(); } }}>
          {content}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
