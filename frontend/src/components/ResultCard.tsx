"use client";

import { useT } from "@/i18n";

type TaskType = "analyze" | "critique" | "iterate";

interface Props {
  data: Record<string, unknown>;
  taskType: TaskType;
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

export default function ResultCard({ data, taskType }: Props) {
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
        <div className="space-y-3">
          {data.directions.map(
            (d: { title: string; description: string; expected_impact: string }, i: number) => (
              <div key={i} className="rounded border border-gray-100 bg-gray-50 p-3">
                <h3 className="text-sm font-semibold text-gray-800">{i + 1}. {d.title}</h3>
                <p className="mt-1 text-sm text-gray-600">{d.description}</p>
                <p className="mt-1 text-xs text-gray-400">{t.result.impact}: {d.expected_impact}</p>
              </div>
            ),
          )}
        </div>
      )}

      {gap && <JudgmentGapCard gap={gap} />}
    </section>
  );
}
