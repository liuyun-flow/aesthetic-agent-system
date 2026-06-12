"use client";

import { useEffect, useState } from "react";
import { useT } from "@/i18n";
import { toDisplayList, isEmptyValue } from "@/lib/formatters";

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
  selected_direction: string | null;
  prompt_result: Record<string, unknown> | null;
}

interface Props {
  refreshKey: number;
  onRetrain?: (description: string, recordType: string) => void;
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

const DIRECTION_DETAIL_LABELS: Record<string, string> = {
  goal: "目标",
  description: "说明",
  visual_changes: "视觉改动",
  color_changes: "色彩改动",
  typography_changes: "字体改动",
  layout_changes: "版式改动",
  commercial_rationale: "商业理由",
  risk: "风险",
};

const PROMPT_FIELDS: Array<[string, string]> = [
  ["chinese_prompt", "中文提示词"],
  ["english_prompt", "英文提示词"],
  ["negative_prompt", "反向提示词"],
  ["design_notes", "设计师执行说明"],
  ["copywriting_prompt", "文案优化提示"],
  ["usage_tips", "使用建议"],
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function valueToText(value: unknown): string {
  if (isEmptyValue(value)) return "";
  if (Array.isArray(value)) {
    return value.map((item) => valueToText(item)).filter(Boolean).join("\n");
  }
  if (isRecord(value)) {
    return JSON.stringify(value, null, 2);
  }
  return String(value);
}

function parseDirection(value: string | null): Record<string, unknown> | null {
  if (!value) return null;
  try {
    const parsed = JSON.parse(value);
    return isRecord(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

function getDirectionId(direction: Record<string, unknown>, index: number): string {
  const id = valueToText(direction.id).trim();
  return id || `direction-${index + 1}`;
}

function copyText(text: string): void {
  navigator.clipboard.writeText(text).catch(() => {});
}

export default function SessionList({ refreshKey, onRetrain }: Props) {
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
        if (!res.ok) throw new Error(t.common.loadSessionsFailed);
        const data = await res.json();
        if (!cancelled) setSessions(data.sessions ?? []);
      } catch (err: unknown) {
        if (!cancelled) setError(err instanceof Error ? err.message : t.common.loadError);
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
      if (!res.ok) throw new Error(t.common.notFound);
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

  /** Fields that should be displayed as a bullet list (JSON string arrays). */
  const LIST_FIELDS = new Set([
    "user_strengths", "user_weaknesses", "user_priority_fixes",
    "ai_main_problems", "ai_priority_fixes", "training_focus_tags",
  ]);

  /** Render a value: list fields get bullet points, scalars get plain text. */
  const renderValue = (key: string, value: unknown) => {
    if (isEmptyValue(value)) return <span className="text-gray-400">暂无</span>;
    if (LIST_FIELDS.has(key)) {
      const items = toDisplayList(value);
      if (items.length === 0) return <span className="text-gray-400">暂无</span>;
      return (
        <ul className="list-inside list-disc space-y-0.5">
          {items.map((item, i) => (
            <li key={i} className="text-gray-700">{item}</li>
          ))}
        </ul>
      );
    }
    const text = valueToText(value);
    return text
      ? <span className="text-gray-700 whitespace-pre-wrap">{text}</span>
      : <span className="text-gray-400">暂无</span>;
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
                        if (isEmptyValue(value)) return null;
                        return (
                          <div key={key}>
                            <span className="text-xs font-medium text-gray-500">{FIELD_LABELS[key] ?? key}</span>
                            <div className="mt-0.5">{renderValue(key, value)}</div>
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
                        if (isEmptyValue(value)) return null;
                        return (
                          <div key={key}>
                            <span className="text-xs font-medium text-gray-500">{FIELD_LABELS[key]}</span>
                            <div className="mt-0.5">{renderValue(key, value)}</div>
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
                    {!isEmptyValue(detail.training_focus_tags) && (
                      <div>
                        <span className="text-xs font-medium text-gray-500">{FIELD_LABELS.training_focus_tags}</span>
                        <div className="mt-0.5">{renderValue("training_focus_tags", detail.training_focus_tags)}</div>
                      </div>
                    )}
                  </Section>
                )}

                {/* V1.7.2: Selected direction + generated prompt */}
                {(() => {
                  const rawDirections = detail.result_json?.directions;
                  if (!Array.isArray(rawDirections)) return null;
                  const directions = rawDirections.filter(isRecord);
                  if (directions.length === 0) return null;
                  const selectedDirection = parseDirection(detail.selected_direction);
                  const selectedId = selectedDirection ? valueToText(selectedDirection.id).trim() : "";

                  return (
                    <Section title="当时所有迭代方向">
                      <div className="space-y-2">
                        {directions.map((direction, index) => {
                          const directionId = getDirectionId(direction, index);
                          const isSelected = selectedId !== "" && directionId === selectedId;

                          return (
                            <div
                              key={`${directionId}-${index}`}
                              className={`rounded border p-3 ${
                                isSelected
                                  ? "border-blue-300 bg-blue-50"
                                  : "border-gray-200 bg-gray-50"
                              }`}
                            >
                              <div className="mb-1 flex items-center gap-2">
                                <span className="text-xs text-gray-400">[{directionId}]</span>
                                <span className="text-sm font-semibold text-gray-700">
                                  {valueToText(direction.title) || `方向 ${index + 1}`}
                                </span>
                                {isSelected && (
                                  <span className="rounded bg-blue-600 px-1.5 py-0.5 text-[11px] text-white">
                                    已选择
                                  </span>
                                )}
                              </div>
                              <div className="space-y-1">
                                {Object.entries(DIRECTION_DETAIL_LABELS).map(([key, label]) => {
                                  const text = valueToText(direction[key]);
                                  if (!text) return null;
                                  return (
                                    <p key={key} className="text-xs text-gray-600">
                                      <span className="font-medium text-gray-500">{label}：</span>
                                      <span className="whitespace-pre-wrap">{text}</span>
                                    </p>
                                  );
                                })}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </Section>
                  );
                })()}

                {detail.selected_direction && (
                  <Section title="选择的迭代方向">
                    {(() => {
                      const direction = parseDirection(detail.selected_direction);
                      if (!direction) {
                        return (
                          <p className="text-sm text-gray-700 whitespace-pre-wrap">
                            {detail.selected_direction}
                          </p>
                        );
                      }
                      return (
                        <div className="space-y-1">
                          <p className="text-sm font-semibold text-gray-700">
                            {valueToText(direction.id) && (
                              <span className="text-xs text-gray-400 mr-1">
                                [{valueToText(direction.id)}]
                              </span>
                            )}
                            {valueToText(direction.title)}
                          </p>
                          {Object.entries(DIRECTION_DETAIL_LABELS).map(([key, label]) => {
                            const text = valueToText(direction[key]);
                            if (!text) return null;
                            return (
                              <p key={key} className="text-xs text-gray-600">
                                <span className="font-medium text-gray-500">{label}：</span>
                                <span className="whitespace-pre-wrap">{text}</span>
                              </p>
                            );
                          })}
                        </div>
                      );
                    })()}
                  </Section>
                )}

                {detail.prompt_result && (
                  <Section title="生成的提示词">
                    <div className="space-y-2 text-sm">
                      {PROMPT_FIELDS.map(([key, label]) => {
                        const text = valueToText(detail.prompt_result?.[key]);
                        if (!text) return null;
                        return (
                          <div key={key}>
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs font-medium text-gray-500">{label}</span>
                              <button
                                onClick={() => handleCopy(text, `hist-${key}`)}
                                className="rounded border border-gray-300 px-2 py-0.5 text-xs text-gray-500 hover:bg-gray-100"
                              >
                                {copiedKey === `hist-${key}` ? "已复制" : "复制"}
                              </button>
                            </div>
                            <pre className="whitespace-pre-wrap rounded bg-gray-50 p-2 text-xs text-gray-700 max-h-32 overflow-y-auto">
                              {text}
                            </pre>
                          </div>
                        );
                      })}
                    </div>
                  </Section>
                )}

                {/* Actions */}
                <div className="flex gap-2 pt-2 border-t">
                  {onRetrain && (
                    <button
                      onClick={() => {
                        onRetrain(detail.work_description, detail.record_type);
                        closeDetail();
                      }}
                      className="rounded bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700"
                      title={t.sessions.retrainHint}
                    >
                      {t.sessions.retrain}
                    </button>
                  )}
                  {detail.result_json && (
                    <button onClick={() => handleCopy(JSON.stringify(detail.result_json, null, 2), "result_json")}
                      className="rounded border border-gray-300 px-3 py-1 text-xs text-gray-600 hover:bg-gray-100">
                      {copiedKey === "result_json" ? "已复制" : "复制完整结果"}
                    </button>
                  )}
                </div>
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
