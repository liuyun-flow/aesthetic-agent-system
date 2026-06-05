"use client";

import { useEffect, useState } from "react";
import { useT } from "@/i18n";

interface Session {
  id: number;
  record_type: string;
  work_description: string;
  created_at: string;
  user_score: number | null;
  ai_score: number | null;
  judgment_gap_summary: string | null;
  training_focus_tags: string | null;
}

/** Full detail returned by GET /sessions/{id} */
interface SessionDetail {
  id: number;
  record_type: string;
  work_description: string;
  created_at: string | null;
  user_score: number | null;
  user_strengths: string | null;
  user_weaknesses: string | null;
  user_priority_fixes: string | null;
  user_target_audience: string | null;
  user_price_band: string | null;
  result_json: Record<string, unknown> | null;
  ai_score: number | null;
  ai_main_problems: string | null;
  ai_priority_fixes: string | null;
  judgment_gap_summary: string | null;
  training_focus_tags: string | null;
}

interface Props {
  refreshKey: number;
}

const FIELD_LABELS: Record<string, string> = {
  user_score: "用户评分",
  user_strengths: "我认为的优点",
  user_weaknesses: "我认为的缺点",
  user_priority_fixes: "我认为的优先修改",
  user_target_audience: "目标用户",
  user_price_band: "价格带",
  ai_score: "AI 评分",
  ai_main_problems: "AI 主要问题",
  ai_priority_fixes: "AI 优先修改",
  judgment_gap_summary: "判断差异总结",
  training_focus_tags: "训练重点标签",
};

function copyText(text: string): void {
  navigator.clipboard.writeText(text).catch(() => {});
}

export default function SessionList({ refreshKey }: Props) {
  const { t } = useT();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Detail modal
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<SessionDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

  useEffect(() => {
    let cancelled = false;
    async function fetchSessions() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${base}/sessions?limit=30`);
        if (!res.ok) throw new Error("Failed to load sessions");
        const data = await res.json();
        if (!cancelled) setSessions(data.sessions ?? []);
      } catch (err: unknown) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Load error");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchSessions();
    return () => { cancelled = true; };
  }, [refreshKey, base]);

  const openDetail = async (id: number) => {
    setSelectedId(id);
    setDetail(null);
    setDetailError(null);
    setDetailLoading(true);
    try {
      const res = await fetch(`${base}/sessions/${id}`);
      if (!res.ok) throw new Error("Not found");
      setDetail(await res.json());
    } catch (err: unknown) {
      setDetailError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setDetailLoading(false);
    }
  };

  const closeDetail = () => {
    setSelectedId(null);
    setDetail(null);
    setDetailError(null);
  };

  const handleCopy = (text: string, key: string) => {
    copyText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const safeStr = (v: unknown): string => {
    if (v === null || v === undefined) return "暂无";
    return String(v);
  };

  const showField = (key: string, value: unknown) => {
    if (value === null || value === undefined) return false;
    if (typeof value === "string" && value.trim() === "") return false;
    if (Array.isArray(value) && value.length === 0) return false;
    return true;
  };

  if (loading && sessions.length === 0) {
    return <section className="text-sm text-gray-400">{t.sessions.loading}</section>;
  }
  if (error) {
    return <section className="text-sm text-red-500">{t.sessions.error}</section>;
  }
  if (sessions.length === 0) {
    return <section className="text-sm text-gray-400">{t.sessions.noSessions}</section>;
  }

  return (
    <>
      <section>
        <h2 className="mb-3 text-base font-semibold text-gray-800">{t.sessions.recentSessions}</h2>
        <div className="space-y-2">
          {sessions.map((s) => (
            <div
              key={s.id}
              onClick={() => openDetail(s.id)}
              className="flex cursor-pointer items-start gap-3 rounded border bg-white px-3 py-2 text-sm
                         hover:border-blue-300 hover:bg-blue-50 transition"
              title="点击查看详情"
            >
              <span className={`mt-0.5 rounded px-1.5 py-0.5 text-xs font-medium ${
                s.record_type === "analyze" ? "bg-purple-100 text-purple-700"
                : s.record_type === "critique" ? "bg-amber-100 text-amber-700"
                : "bg-emerald-100 text-emerald-700"
              }`}>
                {t.tasks[s.record_type as keyof typeof t.tasks]?.label ?? s.record_type}
              </span>
              <span className="flex-1 truncate text-gray-600">{s.work_description}</span>
              {s.judgment_gap_summary && (
                <span className="text-xs text-purple-500">⚡</span>
              )}
              <span className="text-xs text-blue-400 whitespace-nowrap">查看详情 →</span>
              <span className="text-xs text-gray-400">
                {new Date(s.created_at).toLocaleString("zh-CN")}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Detail Modal */}
      {selectedId !== null && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-10 bg-black/40"
             onClick={closeDetail}>
          <div className="relative max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6 shadow-xl"
               onClick={(e) => e.stopPropagation()}>
            <button onClick={closeDetail}
              className="absolute right-4 top-4 text-gray-400 hover:text-gray-600 text-xl leading-none">
              ✕
            </button>

            {detailLoading && (
              <p className="text-sm text-gray-400">正在加载历史详情...</p>
            )}
            {detailError && (
              <p className="text-sm text-red-500">历史详情加载失败</p>
            )}

            {detail && (
              <div className="space-y-5 text-sm">
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">训练详情</h3>
                  <div className="flex gap-3 text-xs text-gray-500">
                    <span className={`rounded px-2 py-0.5 font-medium ${
                      detail.record_type === "analyze" ? "bg-purple-100 text-purple-700"
                      : detail.record_type === "critique" ? "bg-amber-100 text-amber-700"
                      : "bg-emerald-100 text-emerald-700"
                    }`}>
                      {t.tasks[detail.record_type as keyof typeof t.tasks]?.label ?? detail.record_type}
                    </span>
                    <span>{detail.created_at ? new Date(detail.created_at).toLocaleString("zh-CN") : ""}</span>
                  </div>
                </div>

                {/* Work description */}
                <Section title="作品描述">
                  <p className="whitespace-pre-wrap text-gray-700">{detail.work_description}</p>
                </Section>

                {/* User judgment */}
                {(detail.user_score || detail.user_strengths || detail.user_weaknesses) && (
                  <Section title="用户初步判断">
                    <div className="space-y-2">
                      {(["user_score", "user_strengths", "user_weaknesses", "user_priority_fixes", "user_target_audience", "user_price_band"] as const).map((key) => {
                        const value = detail[key as keyof SessionDetail];
                        if (!showField(key, value)) return null;
                        return (
                          <div key={key}>
                            <span className="text-xs font-medium text-gray-500">{FIELD_LABELS[key] ?? key}</span>
                            <p className="text-gray-700 whitespace-pre-wrap">{safeStr(value)}</p>
                          </div>
                        );
                      })}
                    </div>
                  </Section>
                )}

                {/* AI Result */}
                {detail.result_json && (
                  <Section title="AI 分析结果">
                    <div className="space-y-2">
                      {(["ai_score", "ai_main_problems", "ai_priority_fixes"] as const).map((key) => {
                        const value = detail[key as keyof SessionDetail];
                        if (!showField(key, value)) return null;
                        return (
                          <div key={key}>
                            <span className="text-xs font-medium text-gray-500">{FIELD_LABELS[key]}</span>
                            <p className="text-gray-700 whitespace-pre-wrap">{safeStr(value)}</p>
                          </div>
                        );
                      })}
                      {/* Show result_json keys if no ai_ fields */}
                      {!detail.ai_main_problems && !detail.ai_priority_fixes && (
                        <pre className="whitespace-pre-wrap rounded bg-gray-50 p-2 text-xs text-gray-600 max-h-60 overflow-y-auto">
                          {JSON.stringify(detail.result_json, null, 2)}
                        </pre>
                      )}
                    </div>
                  </Section>
                )}

                {/* Judgment gap */}
                {(detail.judgment_gap_summary || detail.training_focus_tags) && (
                  <Section title="判断差异分析">
                    {detail.judgment_gap_summary && (
                      <div className="mb-2">
                        <span className="text-xs font-medium text-gray-500">{FIELD_LABELS.judgment_gap_summary}</span>
                        <p className="text-gray-700 whitespace-pre-wrap">{detail.judgment_gap_summary}</p>
                      </div>
                    )}
                    {detail.training_focus_tags && (
                      <div>
                        <span className="text-xs font-medium text-gray-500">{FIELD_LABELS.training_focus_tags}</span>
                        <p className="text-gray-700 whitespace-pre-wrap">
                          {(() => {
                            try { return JSON.parse(detail.training_focus_tags).join("；"); }
                            catch { return detail.training_focus_tags; }
                          })()}
                        </p>
                      </div>
                    )}
                  </Section>
                )}

                {/* Copy result_json */}
                {detail.result_json && (
                  <div className="flex gap-2 pt-2 border-t">
                    <button onClick={() => handleCopy(JSON.stringify(detail.result_json, null, 2), "result_json")}
                      className="rounded border border-gray-300 px-3 py-1 text-xs text-gray-600 hover:bg-gray-100">
                      {copiedKey === "result_json" ? "已复制" : "复制完整结果"}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500 border-b pb-1">
        {title}
      </h4>
      {children}
    </div>
  );
}
