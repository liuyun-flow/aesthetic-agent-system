"use client";

import { useState, useEffect } from "react";

interface AuditIssue {
  id: number;
  title: string;
  aesthetic_level: string | null;
  completeness_score: number;
  missing_fields: string[];
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

function completenessColor(score: number): string {
  if (score >= 75) return "text-green-600";
  if (score >= 50) return "text-amber-600";
  return "text-red-600";
}

function completenessBg(score: number): string {
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
  items: AuditIssue[];
  emptyMessage: string;
}) {
  if (items.length === 0) {
    return (
      <div className="rounded border bg-gray-50 p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-1">{title}</h4>
        <p className="text-xs text-green-600">{emptyMessage}</p>
      </div>
    );
  }
  return (
    <div className="rounded border bg-gray-50 p-4">
      <h4 className="text-sm font-medium text-gray-700 mb-2">
        {title}
        <span className="ml-1 text-xs text-red-500 font-normal">
          ({items.length} 个)
        </span>
      </h4>
      <div className="space-y-1.5 max-h-60 overflow-y-auto">
        {items.map((item) => (
          <div
            key={item.id}
            className="flex items-center gap-2 text-xs bg-white rounded border px-2 py-1"
          >
            <span
              className={`rounded-full px-1.5 py-0.5 font-medium text-xs ${completenessBg(
                item.completeness_score
              )} ${completenessColor(item.completeness_score)}`}
            >
              {item.completeness_score}
            </span>
            <span className="flex-1 truncate font-medium">{item.title}</span>
            <span className="text-gray-400 text-xs">
              缺：{item.missing_fields.slice(0, 3).join("、")}
              {item.missing_fields.length > 3
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
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-gray-400">正在分析案例库质量…</p>
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
      ? Math.round((data.training_ready_count / data.total_cases) * 100)
      : 0;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">
            案例库体检报告
          </h2>
          <p className="text-xs text-gray-500 mt-0.5">
            评估参考案例库的数据质量和训练可用性
          </p>
        </div>
        <button
          onClick={fetchAudit}
          className="rounded border border-gray-200 px-3 py-1 text-xs text-gray-500 hover:bg-gray-50 transition"
        >
          刷新报告
        </button>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          label="总案例数"
          value={data.total_cases}
          color="text-gray-700"
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
      {data.recommendations.length > 0 && (
        <div className="rounded border border-blue-200 bg-blue-50 p-4">
          <h3 className="text-sm font-medium text-blue-700 mb-2">建议操作</h3>
          <ul className="space-y-1">
            {data.recommendations.map((rec, i) => (
              <li key={i} className="text-xs text-blue-600 flex items-start gap-1.5">
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
      {data.possible_duplicates.length > 0 && (
        <div className="rounded border border-amber-200 bg-amber-50 p-4">
          <h3 className="text-sm font-medium text-amber-700 mb-2">
            疑似重复案例
            <span className="ml-1 text-xs font-normal">
              （{data.possible_duplicates.length} 组）
            </span>
          </h3>
          <div className="space-y-3">
            {data.possible_duplicates.map((group, gi) => (
              <div
                key={gi}
                className="rounded border border-amber-300 bg-white p-3"
              >
                <p className="text-xs text-gray-500 mb-1.5">
                  检测方式：
                  {group.method === "embedding_similarity"
                    ? "语义相似度"
                    : "标题相似度"}
                </p>
                <div className="space-y-1">
                  {group.cases.map((c) => (
                    <div
                      key={c.id}
                      className="flex items-center gap-2 text-xs bg-amber-50 rounded px-2 py-1"
                    >
                      <span
                        className={`rounded-full px-1.5 py-0.5 font-medium text-xs ${completenessBg(
                          c.completeness_score
                        )} ${completenessColor(c.completeness_score)}`}
                      >
                        {c.completeness_score}
                      </span>
                      <span className="flex-1 truncate">{c.title}</span>
                      <span className="text-gray-400">
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

      {data.possible_duplicates.length === 0 && data.total_cases >= 2 && (
        <div className="rounded border bg-gray-50 p-4 text-center">
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
  return (
    <div className="rounded border bg-white p-4 shadow-sm">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>
        {typeof value === "number" && !Number.isInteger(value)
          ? value.toFixed(1)
          : value}
        {suffix && (
          <span className="text-sm font-normal text-gray-400 ml-1">
            {suffix}
          </span>
        )}
      </p>
    </div>
  );
}
