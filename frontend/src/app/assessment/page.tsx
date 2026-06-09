"use client";

import { useState, useEffect, useCallback } from "react";

// ── Types ─────────────────────────────────────────────────────────────

interface AssessmentOverview {
  total_sessions: number;
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
    stable: "text-blue-600",
    worsening: "text-red-600",
    insufficient_data: "text-gray-400",
  };
  return m[t] ?? "text-gray-400";
}

function severityBadge(s: string): string {
  const m: Record<string, string> = {
    high: "bg-red-100 text-red-700",
    medium: "bg-amber-100 text-amber-700",
    low: "bg-gray-100 text-gray-600",
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
  return m[l] ?? "bg-gray-100 text-gray-500";
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
    <div className="rounded border bg-white p-4 shadow-sm">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>
        {display}
        {suffix && <span className="text-sm font-normal text-gray-400 ml-1">{suffix}</span>}
      </p>
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
    try {
      const res = await fetch(`${base}/assessment/report?days=${days}`);
      if (res.ok) setReport(await res.json());
    } catch { /* ignore */ }
    finally { setReportLoading(false); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  useEffect(() => { fetchReport(reportDays); }, [reportDays, fetchReport]);

  // ── Loading ──────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-gray-400">正在分析训练数据…</p>
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

  const hasData = overview.total_sessions >= 5;

  // ── Insufficient data ─────────────────────────────────────────────

  if (!hasData) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">训练效果评估</h2>
          <p className="text-xs text-gray-500 mt-0.5">基于历史训练记录评估审美判断力进步情况</p>
        </div>
        <div className="rounded border bg-amber-50 p-8 text-center">
          <p className="text-amber-600 text-sm font-medium mb-2">训练数据不足</p>
          <p className="text-amber-500 text-xs">
            建议先完成至少 5 次训练（包含自评和 AI 评分），再回来查看评估结果。
          </p>
          <p className="text-gray-400 text-xs mt-2">
            当前已完成 {overview.total_sessions} 次训练
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
        <h2 className="text-lg font-semibold text-gray-800">训练效果评估</h2>
        <p className="text-xs text-gray-500 mt-0.5">基于历史训练记录评估审美判断力进步情况</p>
      </div>

      {/* Summary */}
      <div className="rounded border bg-blue-50 border-blue-200 p-4">
        <p className="text-sm text-blue-700">{overview.summary}</p>
        {(overview.next_focus ?? []).length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {(overview.next_focus ?? []).map((f, i) => (
              <span key={i} className="rounded-full bg-blue-200 text-blue-700 px-2 py-0.5 text-xs">
                {f}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="总训练次数" value={overview.total_sessions} color="text-gray-700" />
        <StatCard label="最近 7 天" value={overview.sessions_last_7_days} suffix="次" color="text-blue-600" />
        <StatCard label="最近 30 天" value={overview.sessions_last_30_days} suffix="次" color="text-indigo-600" />
        <StatCard label="已完成" value={overview.completed_sessions} color="text-green-600" />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <StatCard label="平均自评" value={overview.average_user_score ?? "--"} suffix="分" color="text-purple-600" />
        <StatCard label="平均 AI 评分" value={overview.average_ai_score ?? "--"} suffix="分" color="text-teal-600" />
        <StatCard label="平均判断差距" value={overview.average_score_gap ?? "--"} suffix="分" color="text-orange-600" />
        <StatCard label="近 7 天差距" value={overview.average_score_gap_last_7 ?? "--"} suffix="分" color="text-amber-600" />
        <StatCard label="差距趋势" value={trendLabel(overview.score_gap_trend)} color={trendColor(overview.score_gap_trend)} />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b">
        {(["mistakes", "dimensions", "report"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-xs font-medium rounded-t transition ${
              tab === t
                ? "bg-white border border-b-white text-blue-600 -mb-px"
                : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
            }`}
          >
            {t === "mistakes" ? "常见误判" : t === "dimensions" ? "能力维度" : "周期复盘"}
          </button>
        ))}
      </div>

      {/* Tab: Mistakes */}
      {tab === "mistakes" && (
        <div className="space-y-3">
          {mistakes.length === 0 ? (
            <p className="text-xs text-green-600 bg-green-50 border border-green-200 rounded p-4">
              未发现明显的误判模式，你的判断比较均衡。
            </p>
          ) : (
            mistakes.map((m, i) => (
              <div key={i} className="rounded border bg-white p-4 shadow-sm">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`rounded px-2 py-0.5 text-xs font-medium ${severityBadge(m.severity)}`}>
                    {severityLabel(m.severity)}严重
                  </span>
                  <h4 className="text-sm font-semibold text-gray-800">{m.mistake_type}</h4>
                  <span className="text-xs text-gray-400">出现 {m.count} 次</span>
                </div>
                <p className="text-xs text-gray-600 mb-1.5">{m.explanation}</p>
                <p className="text-xs text-blue-600 bg-blue-50 rounded px-2 py-1">
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
          {dimensions.map((d) => (
            <div key={d.dimension_key} className="rounded border bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-semibold text-gray-800">{d.dimension_name}</h4>
                  <span className={`rounded px-2 py-0.5 text-xs font-medium ${levelBadge(d.level)}`}>
                    {levelLabel(d.level)}
                  </span>
                  <span className="text-xs text-gray-400" title={d.trend}>
                    {dimensionTrendBadge(d.trend)} {d.trend === "insufficient_data" ? "数据不足" : ""}
                  </span>
                </div>
                <span className="text-lg font-bold text-gray-700">{d.score}</span>
              </div>
              {/* Progress bar */}
              <div className="w-full bg-gray-100 rounded-full h-2 mb-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    d.score >= 70 ? "bg-green-500" : d.score >= 45 ? "bg-amber-500" : "bg-red-500"
                  }`}
                  style={{ width: `${Math.max(5, d.score)}%` }}
                />
              </div>
              <p className="text-xs text-gray-500">{d.evidence}</p>
              <p className="text-xs text-blue-600 mt-1">{d.suggestion}</p>
            </div>
          ))}
        </div>
      )}

      {/* Tab: Report */}
      {tab === "report" && (
        <div className="space-y-4">
          {/* Day selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">复盘周期：</span>
            {[7, 30].map((d) => (
              <button
                key={d}
                onClick={() => setReportDays(d)}
                className={`rounded px-3 py-1 text-xs font-medium transition ${
                  reportDays === d
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {d} 天
              </button>
            ))}
          </div>

          {reportLoading ? (
            <p className="text-xs text-gray-400 py-4">正在生成复盘报告…</p>
          ) : report ? (
            <>
              {/* Progress summary */}
              <div className="rounded border bg-green-50 border-green-200 p-4">
                <p className="text-sm text-green-700">{report.progress_summary}</p>
              </div>

              {/* Score gap */}
              <div className="rounded border bg-white p-4 shadow-sm">
                <h4 className="text-sm font-semibold text-gray-700 mb-1">判断准确度</h4>
                <p className="text-xs text-gray-600">{report.score_gap_summary}</p>
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
                <div className="rounded border bg-white p-4 shadow-sm">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">高频误判</h4>
                  <div className="space-y-2">
                    {(report.top_mistakes ?? []).map((m, i) => (
                      <p key={i} className="text-xs text-gray-600">
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
                <div className="rounded border bg-blue-50 border-blue-200 p-4">
                  <h4 className="text-sm font-semibold text-blue-700 mb-2">下一步训练计划</h4>
                  <ul className="space-y-1">
                    {(report.next_training_plan ?? []).map((p, i) => (
                      <li key={i} className="text-xs text-blue-600 flex items-start gap-1.5">
                        <span className="mt-0.5 shrink-0">{i + 1}.</span>
                        <span>{p}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Recommended themes */}
              {(report.recommended_themes ?? []).length > 0 && (
                <div className="rounded border bg-white p-4 shadow-sm">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">推荐训练主题</h4>
                  <div className="flex flex-wrap gap-2">
                    {(report.recommended_themes ?? []).map((t, i) => (
                      <span key={i} className="rounded-full bg-indigo-100 text-indigo-700 px-3 py-1 text-xs font-medium">
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
