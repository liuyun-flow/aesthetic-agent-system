"use client";

import { useState, useEffect, useCallback } from "react";

// ── Types ─────────────────────────────────────────────────────────────

interface AssessmentOverview {
  total_sessions: number;
  valid_scored_sessions: number;
  completed_sessions: number;
  sessions_last_7_days: number;
  sessions_last_30_days: number;
  average_user_score: number | null;
  average_ai_score: number | null;
  average_score_gap: number | null;
  average_score_gap_last_7: number | null;
  average_score_gap_last_30: number | null;
  score_gap_trend: string;
  summary: string;
  next_focus: string[];
  recent_quality_series: number[];
}

interface MistakePattern {
  mistake_type: string;
  count: number;
  severity: string;
  evidence_sessions: number[];
  explanation: string;
  training_suggestion: string;
}

interface DimensionAssessment {
  dimension_key: string;
  dimension_name: string;
  score: number;
  level: string;
  trend: string;
  evidence: string;
  suggestion: string;
}

interface AssessmentReport {
  period_days: number;
  training_count: number;
  score_gap_summary: string;
  top_mistakes: MistakePattern[];
  strongest_dimensions: DimensionAssessment[];
  weakest_dimensions: DimensionAssessment[];
  progress_summary: string;
  next_training_plan: string[];
  recommended_themes: string[];
}

// ── Helpers ────────────────────────────────────────────────────────────

const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

function trendLabel(t: string): string {
  const m: Record<string, string> = {
    improving: "📈 持续进步",
    stable: "📊 保持稳定",
    worsening: "📉 需要关注",
    insufficient_data: "⏳ 数据不足",
  };
  return m[t] ?? t;
}

function trendColor(t: string): string {
  const m: Record<string, string> = {
    improving: "text-green-600",
    stable: "text-accent",
    worsening: "text-red-600",
    insufficient_data: "text-muted",
  };
  return m[t] ?? "text-muted";
}

function severityBadge(s: string): string {
  const m: Record<string, string> = {
    high: "bg-red-100 text-red-700",
    medium: "bg-amber-100 text-amber-700",
    low: "bg-surface-2 text-ink-soft",
  };
  return m[s] ?? m.low;
}

function severityLabel(s: string): string {
  const m: Record<string, string> = { high: "高", medium: "中", low: "低" };
  return m[s] ?? s;
}

function levelBadge(l: string): string {
  const m: Record<string, string> = {
    strong: "bg-green-100 text-green-700",
    medium: "bg-amber-100 text-amber-700",
    weak: "bg-red-100 text-red-700",
  };
  return m[l] ?? "bg-surface-2 text-muted";
}

function levelLabel(l: string): string {
  const m: Record<string, string> = { strong: "优秀", medium: "中等", weak: "薄弱" };
  return m[l] ?? l;
}

function dimensionTrendBadge(t: string): string {
  const m: Record<string, string> = {
    improving: "↑",
    stable: "→",
    worsening: "↓",
    insufficient_data: "?",
  };
  return m[t] ?? "";
}

// ── Components ─────────────────────────────────────────────────────────

function StatCard({
  label, value, suffix, color,
}: {
  label: string; value: number | string; suffix?: string; color: string;
}) {
  // Safely render numeric or string values; never show NaN/Infinity/null/undefined
  const display: string = (() => {
    if (value == null) return "--";
    if (typeof value === "number") {
      if (Number.isNaN(value) || !isFinite(value)) return "--";
      return Number.isInteger(value) ? String(value) : value.toFixed(1);
    }
    if (typeof value === "string") {
      if (value.trim() === "") return "--";
      return value;
    }
    return "--";
  })();
  return (
    <div className="rounded border bg-surface p-4 shadow-soft">
      <p className="text-xs text-muted">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>
        {display}
        {suffix && <span className="text-sm font-normal text-muted ml-1">{suffix}</span>}
      </p>
    </div>
  );
}

/** 7-dimension radar chart, 0-100 per axis. Pure SVG, no dependencies. */
function RadarChart({ dims }: { dims: DimensionAssessment[] }) {
  if (dims.length < 3) return null;

  const cx = 160, cy = 145, R = 95;
  const n = dims.length;
  const angle = (i: number) => (Math.PI * 2 * i) / n - Math.PI / 2;
  const pt = (i: number, r: number): [number, number] => [
    cx + r * Math.cos(angle(i)),
    cy + r * Math.sin(angle(i)),
  ];
  const ring = (frac: number) =>
    dims.map((_, i) => pt(i, R * frac).map((v) => v.toFixed(1)).join(",")).join(" ");
  const dataPoints = dims
    .map((d, i) => pt(i, (Math.max(0, Math.min(100, d.score)) / 100) * R).map((v) => v.toFixed(1)).join(","))
    .join(" ");

  return (
    <div className="rounded border bg-surface p-4 shadow-soft">
      <h4 className="text-sm font-semibold text-ink-soft mb-1">作品维度评分（雷达图）</h4>
      <p className="text-xs text-muted mb-1">你训练作品在各维度的平均质量（AI 评分），非你的判断力分数</p>
      <svg viewBox="0 0 320 300" className="mx-auto w-full max-w-sm" role="img" aria-label="作品维度评分雷达图">
        {/* Grid rings at 25/50/75/100 */}
        {[0.25, 0.5, 0.75, 1].map((f) => (
          <polygon key={f} points={ring(f)} fill="none" stroke="#e5e7eb" strokeWidth="1" />
        ))}
        {/* Axes */}
        {dims.map((_, i) => {
          const [x, y] = pt(i, R);
          return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="#e5e7eb" strokeWidth="1" />;
        })}
        {/* Data */}
        <polygon points={dataPoints} fill="rgba(59,130,246,0.25)" stroke="#3b82f6" strokeWidth="1.5" />
        {dims.map((d, i) => {
          const [x, y] = pt(i, (Math.max(0, Math.min(100, d.score)) / 100) * R);
          return <circle key={i} cx={x} cy={y} r="2.5" fill="#3b82f6" />;
        })}
        {/* Labels */}
        {dims.map((d, i) => {
          const [x, y] = pt(i, R + 16);
          const cos = Math.cos(angle(i));
          const anchor = cos > 0.3 ? "start" : cos < -0.3 ? "end" : "middle";
          return (
            <text key={i} x={x} y={y} textAnchor={anchor} dominantBaseline="middle" fontSize="10" fill="#6b7280">
              {d.dimension_name} {d.score}
            </text>
          );
        })}
      </svg>
    </div>
  );
}

/** Compare overall / 30-day / 7-day judgment gap — smaller is better. */
function GapBars({ overview }: { overview: AssessmentOverview }) {
  const items = [
    { label: "整体平均差距", value: overview.average_score_gap },
    { label: "近 30 天", value: overview.average_score_gap_last_30 },
    { label: "近 7 天", value: overview.average_score_gap_last_7 },
  ].filter((it): it is { label: string; value: number } =>
    typeof it.value === "number" && isFinite(it.value));

  if (items.length < 2) return null;
  const max = Math.max(...items.map((it) => it.value), 1);

  return (
    <div className="rounded border bg-surface p-4 shadow-soft">
      <h4 className="text-sm font-semibold text-ink-soft mb-1">判断差距变化</h4>
      <p className="text-xs text-muted mb-3">自评与 AI 评分的平均差距，越小代表判断越准</p>
      <div className="space-y-2">
        {items.map((it) => (
          <div key={it.label} className="flex items-center gap-2 text-xs">
            <span className="w-24 shrink-0 text-muted">{it.label}</span>
            <div className="h-3 flex-1 rounded bg-surface-2">
              <div
                className={`h-3 rounded ${it.value <= max * 0.5 ? "bg-green-400" : it.value <= max * 0.8 ? "bg-amber-400" : "bg-red-400"}`}
                style={{ width: `${Math.max(4, (it.value / max) * 100)}%` }}
              />
            </div>
            <span className="w-10 text-right font-medium text-ink-soft">{it.value.toFixed(1)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/** Work-quality over time — line of recent ai_overall_score values (0-100). */
function QualityTrend({ series }: { series: number[] }) {
  if (!series || series.length < 2) return null;

  const W = 300, H = 120, padX = 10, padY = 14;
  const n = series.length;
  const maxV = 100, minV = 0;
  const x = (i: number) => padX + (i * (W - 2 * padX)) / (n - 1);
  const y = (v: number) => padY + (1 - (v - minV) / (maxV - minV)) * (H - 2 * padY);
  const points = series.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const last = series[n - 1];
  const first = series[0];
  const delta = last - first;

  return (
    <div className="rounded border bg-surface p-4 shadow-soft">
      <h4 className="text-sm font-semibold text-ink-soft mb-1">作品质量趋势</h4>
      <p className="text-xs text-muted mb-2">
        最近 {n} 次评分作品的 AI 总分（0-100）·
        <span className={delta >= 0 ? "text-green-600" : "text-red-600"}>
          {" "}{delta >= 0 ? "↑" : "↓"} {Math.abs(delta)}
        </span>
      </p>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="作品质量趋势折线图">
        {[25, 50, 75].map((g) => (
          <line key={g} x1={padX} y1={y(g)} x2={W - padX} y2={y(g)} stroke="#f3f4f6" strokeWidth="1" />
        ))}
        <polyline points={points} fill="none" stroke="#6366f1" strokeWidth="2" />
        {series.map((v, i) => (
          <circle key={i} cx={x(i)} cy={y(v)} r="2.5" fill="#6366f1" />
        ))}
      </svg>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────

export default function AssessmentPage() {
  const [overview, setOverview] = useState<AssessmentOverview | null>(null);
  const [mistakes, setMistakes] = useState<MistakePattern[]>([]);
  const [dimensions, setDimensions] = useState<DimensionAssessment[]>([]);
  const [report, setReport] = useState<AssessmentReport | null>(null);
  const [reportDays, setReportDays] = useState(7);
  const [loading, setLoading] = useState(true);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"mistakes" | "dimensions" | "report">("mistakes");

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [ovRes, miRes, diRes] = await Promise.all([
        fetch(`${base}/assessment/overview`),
        fetch(`${base}/assessment/mistakes`),
        fetch(`${base}/assessment/dimensions`),
      ]);
      if (!ovRes.ok || !miRes.ok || !diRes.ok) {
        throw new Error("获取评估数据失败");
      }
      setOverview(await ovRes.json());
      setMistakes(await miRes.json());
      setDimensions(await diRes.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "获取评估数据失败");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchReport = useCallback(async (days: number) => {
    setReportLoading(true);
    setReportError(null);
    try {
      const res = await fetch(`${base}/assessment/report?days=${days}`);
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.detail || `请求失败 (${res.status})`);
      }
      setReport(await res.json());
    } catch (err: unknown) {
      setReportError(err instanceof Error ? err.message : "复盘报告生成失败");
    } finally {
      setReportLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  useEffect(() => { fetchReport(reportDays); }, [reportDays, fetchReport]);

  // ── Loading ──────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-muted">正在分析训练数据…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded border border-red-200 bg-red-50 p-6 text-center">
        <p className="text-red-600 text-sm mb-2">获取评估数据失败</p>
        <p className="text-red-400 text-xs mb-3">{error}</p>
        <button onClick={fetchAll} className="rounded bg-red-600 px-4 py-1 text-xs text-white hover:bg-red-700">重试</button>
      </div>
    );
  }

  if (!overview) return null;

  const hasData = (overview.valid_scored_sessions ?? 0) >= 5;

  // ── Insufficient data ─────────────────────────────────────────────

  if (!hasData) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-lg font-semibold text-ink">训练效果评估</h2>
          <p className="text-xs text-muted mt-0.5">基于历史训练记录评估审美判断力进步情况</p>
        </div>
        <div className="rounded border bg-amber-50 p-8 text-center">
          <p className="text-amber-600 text-sm font-medium mb-2">训练数据不足</p>
          <p className="text-amber-500 text-xs">
            建议先完成至少 5 次训练（包含自评和 AI 评分），再回来查看评估结果。
          </p>
          <p className="text-muted text-xs mt-2">
            当前共 {overview.total_sessions} 条记录，其中 {overview.valid_scored_sessions ?? 0} 条有效评分
          </p>
        </div>
      </div>
    );
  }

  // ── Main dashboard ────────────────────────────────────────────────

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold text-ink">训练效果评估</h2>
        <p className="text-xs text-muted mt-0.5">基于历史训练记录评估审美判断力进步情况</p>
      </div>

      {/* Summary */}
      <div className="rounded border bg-accent-wash border-accent-soft p-4">
        <p className="text-sm text-accent">{overview.summary}</p>
        {(overview.next_focus ?? []).length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {(overview.next_focus ?? []).map((f, i) => (
              <span key={i} className="rounded-full bg-accent-soft text-accent px-2 py-0.5 text-xs">
                {f}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="总训练次数" value={overview.total_sessions} color="text-ink-soft" />
        <StatCard label="最近 7 天" value={overview.sessions_last_7_days} suffix="次" color="text-accent" />
        <StatCard label="最近 30 天" value={overview.sessions_last_30_days} suffix="次" color="text-ink-soft" />
        <StatCard label="已完成" value={overview.completed_sessions} color="text-green-600" />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <StatCard label="平均自评" value={overview.average_user_score ?? "--"} suffix="分" color="text-accent" />
        <StatCard label="平均 AI 评分" value={overview.average_ai_score ?? "--"} suffix="分" color="text-ink-soft" />
        <StatCard label="平均判断差距" value={overview.average_score_gap ?? "--"} suffix="分" color="text-orange-600" />
        <StatCard label="近 7 天差距" value={overview.average_score_gap_last_7 ?? "--"} suffix="分" color="text-amber-600" />
        <StatCard label="差距趋势" value={trendLabel(overview.score_gap_trend)} color={trendColor(overview.score_gap_trend)} />
      </div>

      {/* Charts */}
      <div className="grid gap-3 md:grid-cols-2">
        <RadarChart dims={dimensions} />
        <GapBars overview={overview} />
      </div>
      {(overview.recent_quality_series ?? []).length >= 2 && (
        <QualityTrend series={overview.recent_quality_series} />
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b">
        {(["mistakes", "dimensions", "report"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-xs font-medium rounded-t transition ${
              tab === t
                ? "bg-surface border border-b-white text-accent -mb-px"
                : "text-muted hover:text-ink-soft hover:bg-surface-2"
            }`}
          >
            {t === "mistakes" ? "常见误判" : t === "dimensions" ? "作品维度" : "周期复盘"}
          </button>
        ))}
      </div>

      {/* Tab: Mistakes */}
      {tab === "mistakes" && (
        <div className="space-y-3">
          <p className="text-xs text-muted">
            ⚙️ 误判检测基于关键词启发式规则（非语义分析），仅供参考方向，不是精确诊断。
          </p>
          {mistakes.length === 0 ? (
            <p className="text-xs text-green-600 bg-green-50 border border-green-200 rounded p-4">
              未发现明显的误判模式，你的判断比较均衡。
            </p>
          ) : (
            mistakes.map((m, i) => (
              <div key={i} className="rounded border bg-surface p-4 shadow-soft">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`rounded px-2 py-0.5 text-xs font-medium ${severityBadge(m.severity)}`}>
                    {severityLabel(m.severity)}严重
                  </span>
                  <h4 className="text-sm font-semibold text-ink">{m.mistake_type}</h4>
                  <span className="text-xs text-muted">出现 {m.count} 次</span>
                </div>
                <p className="text-xs text-ink-soft mb-1.5">{m.explanation}</p>
                <p className="text-xs text-accent bg-accent-wash rounded px-2 py-1">
                  💡 {m.training_suggestion}
                </p>
              </div>
            ))
          )}
        </div>
      )}

      {/* Tab: Dimensions */}
      {tab === "dimensions" && (
        <div className="space-y-3">
          <p className="text-xs text-muted">
            这些分数是 AI 对你训练作品在各维度的<b>平均质量评分</b>（0-100），反映你练习作品的水平与趋势，
            而非直接衡量你的判断力。判断力差距见上方「平均判断差距」与差距趋势。
          </p>
          {dimensions.map((d) => (
            <div key={d.dimension_key} className="rounded border bg-surface p-4 shadow-soft">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-semibold text-ink">{d.dimension_name}</h4>
                  <span className={`rounded px-2 py-0.5 text-xs font-medium ${levelBadge(d.level)}`}>
                    {levelLabel(d.level)}
                  </span>
                  <span className="text-xs text-muted" title={d.trend}>
                    {dimensionTrendBadge(d.trend)} {d.trend === "insufficient_data" ? "数据不足" : ""}
                  </span>
                </div>
                <span className="text-lg font-bold text-ink-soft">{d.score}</span>
              </div>
              {/* Progress bar */}
              <div className="w-full bg-surface-2 rounded-full h-2 mb-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    d.score >= 70 ? "bg-green-500" : d.score >= 45 ? "bg-amber-500" : "bg-red-500"
                  }`}
                  style={{ width: `${Math.max(5, d.score)}%` }}
                />
              </div>
              <p className="text-xs text-muted">{d.evidence}</p>
              <p className="text-xs text-accent mt-1">{d.suggestion}</p>
            </div>
          ))}
        </div>
      )}

      {/* Tab: Report */}
      {tab === "report" && (
        <div className="space-y-4">
          {/* Day selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted">复盘周期：</span>
            {[7, 30].map((d) => (
              <button
                key={d}
                onClick={() => setReportDays(d)}
                className={`rounded px-3 py-1 text-xs font-medium transition ${
                  reportDays === d
                    ? "bg-accent text-white"
                    : "bg-surface-2 text-ink-soft hover:bg-gray-200"
                }`}
              >
                {d} 天
              </button>
            ))}
          </div>

          {reportError && (
            <div className="rounded border border-red-200 bg-red-50 p-4 text-center">
              <p className="text-red-600 text-xs mb-2">复盘报告生成失败</p>
              <p className="text-red-400 text-xs">{reportError}</p>
            </div>
          )}
          {reportLoading ? (
            <p className="text-xs text-muted py-4">正在生成复盘报告…</p>
          ) : report ? (
            <>
              {/* Progress summary */}
              <div className="rounded border bg-green-50 border-green-200 p-4">
                <p className="text-sm text-green-700">{report.progress_summary}</p>
              </div>

              {/* Score gap */}
              <div className="rounded border bg-surface p-4 shadow-soft">
                <h4 className="text-sm font-semibold text-ink-soft mb-1">判断准确度</h4>
                <p className="text-xs text-ink-soft">{report.score_gap_summary}</p>
              </div>

              {/* Weakest dimensions */}
              {(report.weakest_dimensions ?? []).length > 0 && (
                <div className="rounded border bg-red-50 border-red-200 p-4">
                  <h4 className="text-sm font-semibold text-red-700 mb-2">最弱能力维度</h4>
                  <div className="space-y-2">
                    {(report.weakest_dimensions ?? []).map((d) => (
                      <div key={d.dimension_key} className="flex items-center gap-2 text-xs">
                        <span className={`rounded px-2 py-0.5 font-medium ${levelBadge(d.level)}`}>
                          {d.dimension_name} ({d.score})
                        </span>
                        <span className="text-red-600">{d.suggestion}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Strongest dimensions */}
              {(report.strongest_dimensions ?? []).length > 0 && (
                <div className="rounded border bg-green-50 border-green-200 p-4">
                  <h4 className="text-sm font-semibold text-green-700 mb-2">最强能力维度</h4>
                  <div className="space-y-2">
                    {(report.strongest_dimensions ?? []).map((d) => (
                      <div key={d.dimension_key} className="flex items-center gap-2 text-xs">
                        <span className={`rounded px-2 py-0.5 font-medium bg-green-200 text-green-700`}>
                          {d.dimension_name} ({d.score})
                        </span>
                        <span className="text-green-600">保持优势</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Top mistakes */}
              {(report.top_mistakes ?? []).length > 0 && (
                <div className="rounded border bg-surface p-4 shadow-soft">
                  <h4 className="text-sm font-semibold text-ink-soft mb-2">高频误判</h4>
                  <div className="space-y-2">
                    {(report.top_mistakes ?? []).map((m, i) => (
                      <p key={i} className="text-xs text-ink-soft">
                        <span className={`rounded px-1.5 py-0.5 font-medium mr-1 ${severityBadge(m.severity)}`}>
                          {m.mistake_type}
                        </span>
                        {m.training_suggestion}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* Training plan */}
              {(report.next_training_plan ?? []).length > 0 && (
                <div className="rounded border bg-accent-wash border-accent-soft p-4">
                  <h4 className="text-sm font-semibold text-accent mb-2">下一步训练计划</h4>
                  <ul className="space-y-1">
                    {(report.next_training_plan ?? []).map((p, i) => (
                      <li key={i} className="text-xs text-accent flex items-start gap-1.5">
                        <span className="mt-0.5 shrink-0">{i + 1}.</span>
                        <span>{p}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Recommended themes */}
              {(report.recommended_themes ?? []).length > 0 && (
                <div className="rounded border bg-surface p-4 shadow-soft">
                  <h4 className="text-sm font-semibold text-ink-soft mb-2">推荐训练主题</h4>
                  <div className="flex flex-wrap gap-2">
                    {(report.recommended_themes ?? []).map((t, i) => (
                      <span key={i} className="rounded-full bg-surface-2 text-ink-soft px-3 py-1 text-xs font-medium">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : null}
        </div>
      )}
    </div>
  );
}
