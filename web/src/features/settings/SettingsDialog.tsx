import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CloudDownload, Loader2, Save } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../../api";
import type { Density, Locale, Settings } from "../../types";
import { Modal, SelectControl } from "../../shared/ui";

const text = (locale: Locale, zh: string, en: string) => locale === "zh" ? zh : en;

export function SettingsDialog({
  open,
  onOpenChange,
  locale,
  onApplied
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  locale: Locale;
  onApplied: (settings: Settings) => void;
}) {
  const queryClient = useQueryClient();
  const { data } = useQuery({ queryKey: ["settings"], queryFn: ({ signal }) => api.settings(signal) });
  const [handle, setHandle] = useState("");
  const [nextLocale, setNextLocale] = useState<Locale>(locale);
  const [pageSize, setPageSize] = useState<20 | 50 | 100>(50);
  const [density, setDensity] = useState<Density>("comfortable");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!data) return;
    setHandle(data.codeforces_handle);
    setNextLocale(data.locale);
    setPageSize(data.page_size);
    setDensity(data.density);
  }, [data, open]);

  const saveMutation = useMutation({
    mutationFn: () => api.patchSettings({ codeforces_handle: handle.trim(), locale: nextLocale, page_size: pageSize, density }),
    onSuccess: (settings) => {
      queryClient.setQueryData(["settings"], settings);
      queryClient.invalidateQueries({ queryKey: ["search"] });
      onApplied(settings);
      setMessage(text(locale, "设置已保存", "Settings saved"));
    }
  });
  const syncMutation = useMutation({
    mutationFn: (full: boolean) => api.syncCodeforces(full),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["search"] });
      queryClient.invalidateQueries({ queryKey: ["problem"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      setMessage(text(locale, `同步完成：匹配 ${result.matched_problems} 题`, `Synced ${result.matched_problems} problems`));
    }
  });
  const save = () => {
    if (data && data.codeforces_handle !== handle.trim() && data.codeforces_handle && !window.confirm(text(locale, "更换 handle 会清除旧的同步状态，但保留手动状态和笔记。继续吗？", "Changing handle clears synced progress but keeps manual state and notes. Continue?"))) return;
    saveMutation.mutate();
  };
  const sync = (full: boolean) => {
    if (!handle.trim()) { setMessage(text(locale, "请先填写并保存 Codeforces handle", "Save a Codeforces handle first")); return; }
    if (data && (data.codeforces_handle !== handle.trim() || data.locale !== nextLocale || data.page_size !== pageSize || data.density !== density)) {
      setMessage(text(locale, "请先保存设置，再开始同步", "Save settings before syncing"));
      return;
    }
    if (full && !window.confirm(text(locale, "全量同步会重新构建所有同步状态，继续吗？", "Rebuild all synced progress?"))) return;
    syncMutation.mutate(full);
  };
  const error = saveMutation.error || syncMutation.error;

  return (
    <Modal open={open} onOpenChange={onOpenChange} title={text(locale, "设置", "Settings")} description={text(locale, "管理界面偏好和 Codeforces 同步", "Preferences and Codeforces sync")} className="settings-dialog">
      <div className="settings-form">
        <label className="field"><span>Codeforces handle</span><input value={handle} onChange={(event) => setHandle(event.target.value)} placeholder="tourist" /></label>
        <div className="settings-row"><label><span>{text(locale, "语言", "Language")}</span><SelectControl<Locale> label={text(locale, "语言", "Language")} value={nextLocale} onChange={setNextLocale} options={[{ value: "zh", label: "中文" }, { value: "en", label: "English" }]} /></label><label><span>{text(locale, "每页题数", "Page size")}</span><SelectControl<"20" | "50" | "100"> label={text(locale, "每页题数", "Page size")} value={String(pageSize) as "20" | "50" | "100"} onChange={(value) => setPageSize(Number(value) as 20 | 50 | 100)} options={[20, 50, 100].map((value) => ({ value: String(value) as "20" | "50" | "100", label: String(value) }))} /></label></div>
        <label><span>{text(locale, "界面密度", "Density")}</span><div className="segmented"><button className={density === "comfortable" ? "active" : ""} onClick={() => setDensity("comfortable")}>{text(locale, "舒适", "Comfortable")}</button><button className={density === "compact" ? "active" : ""} onClick={() => setDensity("compact")}>{text(locale, "紧凑", "Compact")}</button></div></label>
        <button className="primary-button" onClick={save} disabled={saveMutation.isPending}>{saveMutation.isPending ? <Loader2 className="spin" size={16} /> : <Save size={16} />}{text(locale, "保存设置", "Save settings")}</button>
      </div>
      <section className="sync-section">
        <h3>{text(locale, "做题记录同步", "Progress sync")}</h3>
        <p>{data?.last_sync_at ? text(locale, `上次同步：${data.last_sync_at}`, `Last sync: ${data.last_sync_at}`) : text(locale, "尚未同步", "Not synced yet")}</p>
        {data?.last_sync_error ? <div className="error-banner">{data.last_sync_error}</div> : null}
        <div><button className="secondary-button" onClick={() => sync(false)} disabled={syncMutation.isPending}><CloudDownload size={16} />{text(locale, "增量同步", "Incremental sync")}</button><button className="text-button" onClick={() => sync(true)} disabled={syncMutation.isPending}>{text(locale, "重新全量同步", "Full resync")}</button></div>
      </section>
      {message ? <div className="success-banner">{message}</div> : null}
      {error ? <div className="error-banner">{(error as Error).message}</div> : null}
    </Modal>
  );
}
