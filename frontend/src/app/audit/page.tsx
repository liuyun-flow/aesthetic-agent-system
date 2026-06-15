"use client";

import { useState, useEffect } from "react";

interface AuditIssue {
  id: number;
  title: string;
  aesthetic_level: string | null;
  completeness_score: number;
  is_training_ready: boolean;
  missing_fields: string[];
  reason: string;
}

interface DuplicateGroup {
  method: string;
  cases: AuditIssue[];
}

interface AuditData {
  total_cases: number;
  training_ready_count: number;
  incomplete_count: number;
  average_completeness: number;
  missing_image: AuditIssue[];
  missing_description: AuditIssue[];
  missing_aesthetic_level: AuditIssue[];
  missing_price_band: AuditIssue[];
  missing_premium_sources: AuditIssue[];
  missing_cheapness_sources: AuditIssue[];
  missing_learning_notes: AuditIssue[];
  possible_duplicates: DuplicateGroup[];
  recommendations: string[];
}

function completenessColor(score: number | null | undefined): string {
  if (score == null || Number.isNaN(score)) return "text-muted";
  if (score >= 75) return "text-green-600";
  if (score >= 50) return "text-amber-600";
  return "text-red-600";
}

function completenessBg(score: number | null | undefined): string {
  if (score == null || Number.isNaN(score)) return "bg-surface-2";
  if (score >= 75) return "bg-green-100";
  if (score >= 50) return "bg-amber-100";
  return "bg-red-100";
}

function IssueList({
  title,
  items,
  emptyMessage,
}: {
  title: string;
  items: AuditIssue[] | null | undefined;
  emptyMessage: string;
}) {
  const safeItems = items ?? [];
  if (safeItems.length === 0) {
    return (
      <div className="rounded border bg-surface-2 p-4">
        <h4 className="text-sm font-medium text-ink-soft mb-1">{title}</h4>
        <p className="text-xs text-green-600">{emptyMessage}</p>
      </div>
    );
  }
  return (
    <div className="rounded border bg-surface-2 p-4">
      <h4 className="text-sm font-medium text-ink-soft mb-2">
        {title}
        <span className="ml-1 text-xs text-red-500 font-normal">
          ({safeItems.length} 个)
        </span>
      </h4>
      <div className="space-y-1.5 max-h-60 overflow-y-auto">
        {safeItems.map((item) => (
          <div
            key={item.id}
            className="flex items-center gap-2 text-xs bg-surface rounded border px-2 py-1"
            title={item.reason || undefined}
          >
            <span
              className={`rounded-full px-1.5 py-0.5 font-medium text-xs ${completenessBg(
                item.completeness_score
              )} ${completenessColor(item.completeness_score)}`}
            >
              {item.completeness_score ?? "?"}
            </span>
            {item.is_training_ready && (
              <span className="text-green-500 font-bold shrink-0" title="训练可用">✓</span>
            )}
            <span className="flex-1 truncate font-medium">{item.title}</span>
            {item.reason && (
              <span className="text-muted text-xs truncate max-w-[200px]" title={item.reason}>
                {item.reason}
              </span>
            )}
            <span className="text-muted text-xs shrink-0">
              缺：{(item.missing_fields ?? []).slice(0, 3).join("、") || "无"}
              {(item.missing_fields ?? []).length > 3
                ? `等${item.missing_fields.length}项`
                : ""}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function AuditPage() {
  const [data, setData] = useState<AuditData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

  const fetchAudit = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${base}/reference-cases/audit`);
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.detail || `请求失败 (${res.status})`);
      }
      setData(await res.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "获取体检数据失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAudit();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-muted">正在分析案例库质量…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded border border-red-200 bg-red-50 p-6 text-center">
        <p className="text-red-600 text-sm mb-2">获取体检数据失败</p>
        <p className="text-red-400 text-xs mb-3">{error}</p>
        <button
          onClick={fetchAudit}
          className="rounded bg-red-600 px-4 py-1 text-xs text-white hover:bg-red-700"
        >
          重试
        </button>
      </div>
    );
  }

  if (!data) return null;

  const readyPct =
    data.total_cases > 0
      ? Math.min(100, Math.max(0, Math.round((data.training_ready_count / data.total_cases) * 100)))
      : 0;

  if (data.total_cases === 0) {
    return (
      <div className="space-y-5">
        <div>
          <h2 className="text-lg font-semibold text-ink">案例库体检报告</h2>
          <p className="text-xs text-muted mt-0.5">评估参考案例库的数据质量和训练可用性</p>
        </div>
        <div className="rounded border bg-surface-2 p-12 text-center">
          <p className="text-muted text-sm mb-2">案例库为空</p>
          <p className="text-muted text-xs">
            请先在训练工作台的参考案例库中添加案例，然后再查看体检报告。
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-ink">
            案例库体检报告
          </h2>
          <p className="text-xs text-muted mt-0.5">
            评估参考案例库的数据质量和训练可用性
          </p>
        </div>
        <button
          onClick={fetchAudit}
          className="rounded border border-line px-3 py-1 text-xs text-muted hover:bg-surface-2 transition"
        >
          刷新报告
        </button>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          label="总案例数"
          value={data.total_cases}
          color="text-ink-soft"
        />
        <StatCard
          label="训练可用"
          value={data.training_ready_count}
          suffix={data.total_cases > 0 ? `${readyPct}%` : undefined}
          color="text-green-600"
        />
        <StatCard
          label="不完整案例"
          value={data.incomplete_count}
          color={data.incomplete_count > 0 ? "text-red-600" : "text-green-600"}
        />
        <StatCard
          label="平均完整度"
          value={data.average_completeness}
          suffix="分"
          color={
            data.average_completeness >= 75
              ? "text-green-600"
              : data.average_completeness >= 50
              ? "text-amber-600"
              : "text-red-600"
          }
        />
      </div>

      {/* Recommendations */}
      {(data.recommendations ?? []).length > 0 && (
        <div className="rounded border border-accent-soft bg-accent-wash p-4">
          <h3 className="text-sm font-medium text-accent mb-2">建议操作</h3>
          <ul className="space-y-1">
            {(data.recommendations ?? []).map((rec, i) => (
              <li key={`rec-${i}`} className="text-xs text-accent flex items-start gap-1.5">
                <span className="mt-0.5 shrink-0">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Issue categories */}
      <div className="grid gap-3 md:grid-cols-2">
        <IssueList
          title="缺少案例图片"
          items={data.missing_image}
          emptyMessage="所有案例都有图片"
        />
        <IssueList
          title="缺少图片描述"
          items={data.missing_description}
          emptyMessage="所有案例都有描述"
        />
        <IssueList
          title="缺少审美等级"
          items={data.missing_aesthetic_level}
          emptyMessage="所有案例都有审美等级"
        />
        <IssueList
          title="缺少价格档位"
          items={data.missing_price_band}
          emptyMessage="所有案例都有价格档位"
        />
        <IssueList
          title="缺少高级感来源"
          items={data.missing_premium_sources}
          emptyMessage="所有案例都有高级感来源"
        />
        <IssueList
          title="缺少廉价感来源"
          items={data.missing_cheapness_sources}
          emptyMessage="所有案例都有廉价感来源"
        />
        <IssueList
          title="缺少学习备注"
          items={data.missing_learning_notes}
          emptyMessage="所有案例都有学习备注"
        />
      </div>

      {/* Duplicates */}
      {(data.possible_duplicates ?? []).length > 0 && (
        <div className="rounded border border-amber-200 bg-amber-50 p-4">
          <h3 className="text-sm font-medium text-amber-700 mb-2">
            疑似重复案例
            <span className="ml-1 text-xs font-normal">
              （{(data.possible_duplicates ?? []).length} 组）
            </span>
          </h3>
          <div className="space-y-3">
            {(data.possible_duplicates ?? []).map((group, gi) => (
              <div
                key={`dup-${gi}`}
                className="rounded border border-amber-300 bg-surface p-3"
              >
                <p className="text-xs text-muted mb-1.5">
                  检测方式：
                  {group.method === "embedding_similarity"
                    ? "语义相似度"
                    : "标题相似度"}
                </p>
                <div className="space-y-1">
                  {(group.cases ?? []).map((c) => (
                    <div
                      key={c.id}
                      className="flex items-center gap-2 text-xs bg-amber-50 rounded px-2 py-1"
                    >
                      <span
                        className={`rounded-full px-1.5 py-0.5 font-medium text-xs ${completenessBg(
                          c.completeness_score
                        )} ${completenessColor(c.completeness_score)}`}
                      >
                        {c.completeness_score ?? "?"}
                      </span>
                      <span className="flex-1 truncate">{c.title}</span>
                      <span className="text-muted">
                        #{c.id}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {(data.possible_duplicates ?? []).length === 0 && data.total_cases >= 2 && (
        <div className="rounded border bg-surface-2 p-4 text-center">
          <p className="text-xs text-green-600">未发现疑似重复案例</p>
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  suffix,
  color,
}: {
  label: string;
  value: number;
  suffix?: string;
  color: string;
}) {
  const safe = (typeof value === "number" && !Number.isNaN(value) && isFinite(value))
    ? value
    : 0;
  const display = typeof safe === "number" && !Number.isInteger(safe)
    ? safe.toFixed(1)
    : String(Math.max(0, safe));
  return (
    <div className="rounded border bg-surface p-4 shadow-soft">
      <p className="text-xs text-muted">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>
        {display}
        {suffix && (
          <span className="text-sm font-normal text-muted ml-1">
            {suffix}
          </span>
        )}
      </p>
    </div>
  );
}
