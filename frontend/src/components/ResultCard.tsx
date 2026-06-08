"use client";

import { useState } from "react";
import { useT } from "@/i18n";

type TaskType = "analyze" | "critique" | "iterate";

export interface DirectionData {
  id: string;
  title: string;
  description: string;
  expected_impact: string;
  goal: string;
  visual_changes: string;
  color_changes: string;
  typography_changes: string;
  layout_changes: string;
  commercial_rationale: string;
  risk: string;
}

interface Props {
  data: Record<string, unknown>;
  taskType: TaskType;
  selectedDirectionId?: string | null;
  onSelectDirection?: (direction: DirectionData) => void;
  onGeneratePrompt?: (direction: DirectionData) => void;
  generatingPrompt?: boolean;
}

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

const DIM_KEYS: Record<string, string> = {
  color: "color", composition: "composition", typography: "typography",
  material: "material", emotion: "emotion", brand_sense: "brandSense",
  premium_sources: "premiumSources", cheapness_sources: "cheapnessSourcesList",
  improvement_suggestions: "improvements", total_score: "totalScore",
  dimensions: "dimensionScores", main_issues: "mainIssues",
  priority_fixes: "priorityFixes",
  directions: "directions",
};

function JudgmentGapCard({ gap }: { gap: Record<string, unknown> }) {
  const { t } = useT();
  const sections: [string, string][] = [
    ["accurate_judgments", t.result.whatYouGotRight],
    ["missed_issues", t.result.whatYouMissed],
    ["misjudgments", t.result.whatYouMisjudged],
    ["commercial_blind_spots", t.result.commercialBlindSpots],
    ["aesthetic_blind_spots", t.result.aestheticBlindSpots],
    ["next_training_focus", t.result.nextTrainingFocus],
  ];

  return (
    <div className="mt-5 rounded border border-purple-200 bg-purple-50 p-4">
      <h3 className="mb-3 text-sm font-semibold text-purple-800">
        {t.result.yourJudgmentVsAI}
      </h3>
      {(gap.short_summary as string) && (
        <p className="mb-3 text-sm text-purple-700">{String(gap.short_summary)}</p>
      )}
      <div className="space-y-3">
        {sections.map(([key, label]) => {
          const value = gap[key];
          if (!Array.isArray(value) || value.length === 0) return null;
          return (
            <div key={key}>
              <h4 className="mb-1 text-xs font-semibold text-purple-600">{label}</h4>
              <ul className="list-inside list-disc space-y-0.5">
                {value.map((item: unknown, i: number) => (
                  <li key={i} className="text-sm text-purple-800">{String(item)}</li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function ResultCard({
  data, taskType, selectedDirectionId, onSelectDirection, onGeneratePrompt, generatingPrompt,
}: Props) {
  const { t } = useT();
  const heading = t.result[taskType === "analyze" ? "analysis" : taskType === "critique" ? "critique" : "iterations"];
  const gap = isRecord(data.judgment_gap) ? data.judgment_gap : null;

  return (
    <section className="rounded border bg-white p-5 shadow-sm">
      <h2 className="mb-4 text-base font-semibold text-gray-800">{heading}</h2>

      {taskType === "analyze" && isRecord(data) && (
        <div className="space-y-4">
          {Object.entries(data).map(([key, value]) => {
            if (key === "judgment_gap") return null;
            return (
              <div key={key}>
                <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">
                  {t.result[DIM_KEYS[key] as keyof typeof t.result] ?? key}
                </h3>
                <p className="text-sm leading-relaxed text-gray-700">
                  {typeof value === "string" ? value : JSON.stringify(value)}
                </p>
              </div>
            );
          })}
        </div>
      )}

      {taskType === "critique" && isRecord(data) && (
        <div className="space-y-4">
          {"total_score" in data && (
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-600">{t.result.totalScore}</span>
              <span className="rounded bg-blue-100 px-2 py-0.5 text-lg font-bold text-blue-700">
                {String(data.total_score)}
              </span>
              <span className="text-xs text-gray-400">{t.result.scoreOutOf}</span>
            </div>
          )}
          {isRecord(data.dimensions) && (
            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                {t.result.dimensionScores}
              </h3>
              <div className="grid grid-cols-3 gap-2">
                {Object.entries(data.dimensions).map(([dim, score]) => (
                  <div key={dim} className="rounded bg-gray-50 px-3 py-2 text-center">
                    <div className="text-xs text-gray-500">
                      {t.result[DIM_KEYS[dim] as keyof typeof t.result] ?? dim}
                    </div>
                    <div className="text-sm font-semibold text-gray-800">{String(score)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {["main_issues", "cheapness_sources", "priority_fixes"].map((field) => {
            const value = data[field];
            if (!Array.isArray(value) || value.length === 0) return null;
            return (
              <div key={field}>
                <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">
                  {t.result[DIM_KEYS[field] as keyof typeof t.result] ?? field}
                </h3>
                <ul className="list-inside list-disc space-y-1">
                  {value.map((item: string, i: number) => (
                    <li key={i} className="text-sm text-gray-700">{item}</li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      )}

      {taskType === "iterate" && Array.isArray(data.directions) && (
        <IterationDirections
          directions={data.directions as unknown as DirectionData[]}
          selectedDirectionId={selectedDirectionId}
          onSelect={onSelectDirection}
          onGenerate={onGeneratePrompt}
          generatingPrompt={generatingPrompt}
          t={t}
        />
      )}

      {gap && <JudgmentGapCard gap={gap} />}
    </section>
  );
}

/* ── V1.7.2: Iteration Direction Cards ─────────────────────────────── */

const FIELD_LABELS_ITER: Record<string, string> = {
  goal: "设计目标",
  visual_changes: "视觉变化",
  color_changes: "色彩变化",
  typography_changes: "字体排版变化",
  layout_changes: "布局变化",
  commercial_rationale: "商业理由",
  risk: "风险提示",
};

function IterationDirections({
  directions,
  selectedDirectionId,
  onSelect,
  onGenerate,
  generatingPrompt,
  t,
}: {
  directions: DirectionData[];
  selectedDirectionId?: string | null;
  onSelect?: (d: DirectionData) => void;
  onGenerate?: (d: DirectionData) => void;
  generatingPrompt?: boolean;
  t: ReturnType<typeof useT>["t"];
}) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <div className="space-y-3">
      {!selectedDirectionId && (
        <p className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded px-3 py-2">
          请先选择一个迭代方向，然后再生成提示词。
        </p>
      )}
      {directions.map((d, i) => {
        const isSelected = selectedDirectionId === d.id;
        const isExpanded = expandedId === d.id;

        return (
          <div
            key={d.id || i}
            className={`rounded border p-3 transition ${
              isSelected
                ? "border-blue-400 bg-blue-50 ring-1 ring-blue-200"
                : "border-gray-200 bg-white hover:border-gray-300"
            }`}
          >
            {/* Header */}
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-gray-800">
                  <span className="text-xs text-gray-400 mr-1">{d.id || `dir-${i + 1}`}</span>
                  {d.title}
                </h3>
                <p className="mt-1 text-sm text-gray-600 line-clamp-2">{d.description}</p>
                {d.expected_impact && (
                  <p className="mt-1 text-xs text-gray-400">
                    {t.result.impact}: {d.expected_impact}
                  </p>
                )}
              </div>
            </div>

            {/* Expandable detail */}
            <button
              onClick={() => setExpandedId(isExpanded ? null : d.id)}
              className="mt-2 text-xs text-blue-600 hover:underline"
            >
              {isExpanded ? "收起详情 ▲" : "展开详情 ▼"}
            </button>

            {isExpanded && (
              <div className="mt-3 space-y-2 border-t pt-3">
                {Object.entries(FIELD_LABELS_ITER).map(([key, label]) => {
                  const raw = (d as unknown as Record<string, unknown>)[key];
                  const val = raw ? String(raw) : "";
                  if (!val) return null;
                  return (
                    <div key={key}>
                      <span className="text-xs font-medium text-gray-500">{label}</span>
                      <p className="text-sm text-gray-700">{val}</p>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Action buttons */}
            <div className="mt-3 flex gap-2">
              {!isSelected && onSelect && (
                <button
                  onClick={() => onSelect(d)}
                  className="rounded bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 transition"
                >
                  选择这个方向
                </button>
              )}
              {isSelected && (
                <span className="rounded bg-blue-100 px-3 py-1.5 text-xs font-medium text-blue-700">
                  ✓ 已选择
                </span>
              )}
              {isSelected && onGenerate && (
                <button
                  onClick={() => onGenerate(d)}
                  disabled={generatingPrompt}
                  className={`rounded px-3 py-1.5 text-xs font-medium text-white transition ${
                    generatingPrompt
                      ? "cursor-not-allowed bg-gray-300"
                      : "bg-indigo-600 hover:bg-indigo-700"
                  }`}
                >
                  {generatingPrompt ? "正在基于该方向生成提示词…" : "基于该方向生成提示词"}
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
