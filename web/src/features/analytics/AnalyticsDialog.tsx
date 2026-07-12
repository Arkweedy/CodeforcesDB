import { useQuery } from "@tanstack/react-query";
import { BarChart3, Loader2 } from "lucide-react";
import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { api } from "../../api";
import type { Locale, SearchParams } from "../../types";
import { Modal } from "../../shared/ui";

const text = (locale: Locale, zh: string, en: string) => locale === "zh" ? zh : en;
const COLORS = ["#8fb8c8", "#e2a13a", "#46a978", "#d96b7d", "#5f9aa8"];

export function AnalyticsDialog({ open, onOpenChange, params, locale }: { open: boolean; onOpenChange: (open: boolean) => void; params: SearchParams; locale: Locale }) {
  const [scope, setScope] = useState<"current" | "global">("current");
  const { data, isLoading, error } = useQuery({
    queryKey: ["analytics", scope, params],
    queryFn: ({ signal }) => api.analytics(params, scope, signal),
    enabled: open
  });
  return (
    <Modal open={open} onOpenChange={onOpenChange} title={text(locale, "题库分析", "Problem analytics")} description={text(locale, "查看当前筛选或全库的分布", "Explore the current or global distribution")} className="analytics-dialog">
      <div className="scope-toggle segmented"><button className={scope === "current" ? "active" : ""} onClick={() => setScope("current")}>{text(locale, "当前筛选", "Current")}</button><button className={scope === "global" ? "active" : ""} onClick={() => setScope("global")}>{text(locale, "全库", "Global")}</button></div>
      {isLoading ? <div className="modal-loading"><Loader2 className="spin" /></div> : null}
      {error ? <div className="error-banner">{(error as Error).message}</div> : null}
      {data ? <div className="analytics-grid">
        <article className="chart-card wide"><h3><BarChart3 size={16} /> Rating</h3><ResponsiveContainer width="100%" height={240}><BarChart data={data.rating_buckets}><CartesianGrid stroke="#e8eef0" vertical={false} /><XAxis dataKey="rating" /><YAxis width={38} /><Tooltip /><Bar dataKey="count" fill="#5f9aa8" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></article>
        <article className="chart-card"><h3>{text(locale, "做题状态", "Progress")}</h3><ResponsiveContainer width="100%" height={220}><PieChart><Pie data={data.progress} dataKey="count" nameKey="name" innerRadius={48} outerRadius={78} paddingAngle={3}>{data.progress.map((_, index) => <Cell key={index} fill={COLORS[index]} />)}</Pie><Tooltip /></PieChart></ResponsiveContainer><ul>{data.progress.map((item, index) => <li key={item.name}><i style={{ background: COLORS[index] }} />{item.name}<strong>{item.count}</strong></li>)}</ul></article>
        <article className="chart-card"><h3>{text(locale, "个人优先级", "Priority")}</h3><ResponsiveContainer width="100%" height={220}><BarChart data={data.priority} layout="vertical"><XAxis type="number" hide /><YAxis dataKey="name" type="category" width={82} /><Tooltip /><Bar dataKey="count" fill="#d96b7d" radius={[0, 4, 4, 0]} /></BarChart></ResponsiveContainer></article>
        <article className="chart-card wide"><h3>{text(locale, "常见标签", "Top tags")}</h3><div className="top-tags-chart">{data.top_tags.map((item) => <div key={item.tag}><span>{item.tag}</span><div><i style={{ width: `${Math.max(4, item.count / Math.max(...data.top_tags.map((entry) => entry.count)) * 100)}%` }} /></div><strong>{item.count}</strong></div>)}</div></article>
      </div> : null}
    </Modal>
  );
}
