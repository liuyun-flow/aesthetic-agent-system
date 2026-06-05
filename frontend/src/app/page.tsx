"use client";

import { useState, useCallback } from "react";
import TaskForm, { type UserJudgment, type ImageData } from "@/components/TaskForm";
import ResultCard from "@/components/ResultCard";
import SessionList from "@/components/SessionList";
import ReferencePanel from "@/components/ReferencePanel";
import { useT } from "@/i18n";

type TaskType = "analyze" | "critique" | "iterate";

export default function Home() {
  const { t } = useT();
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [taskType, setTaskType] = useState<TaskType | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  // V1.4: Compare with references state
  const [comparing, setComparing] = useState(false);
  const [compareResult, setCompareResult] = useState<Record<string, unknown> | null>(null);
  const [compareError, setCompareError] = useState<string | null>(null);
  // Store last submission data for compare
  const [lastDescription, setLastDescription] = useState("");
  const [lastJudgment, setLastJudgment] = useState<UserJudgment | null>(null);
  const [lastImage, setLastImage] = useState<ImageData | null>(null);

  const handleSubmit = useCallback(
    async (description: string, type: TaskType, judgment: UserJudgment | null, image: ImageData | null) => {
      setLoading(true);
      setError(null);
      setResult(null);
      setCompareResult(null);
      setTaskType(type);
      setLastDescription(description);
      setLastJudgment(judgment);
      setLastImage(image);

      try {
        const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
        const body: Record<string, unknown> = { work_description: description };
        if (image) {
          body.image_id = image.image_id;
          if (image.image_description) body.image_description = image.image_description;
        }
        if (judgment) {
          body.user_judgment = {
            score: judgment.score,
            strengths: judgment.strengths.length > 0 ? judgment.strengths : null,
            weaknesses: judgment.weaknesses.length > 0 ? judgment.weaknesses : null,
            priority_fixes: judgment.priority_fixes.length > 0 ? judgment.priority_fixes : null,
            target_audience: judgment.target_audience || null,
            price_band: judgment.price_band || null,
          };
        }

        const res = await fetch(`${base}/${type}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });

        if (!res.ok) {
          const errBody = await res.json().catch(() => ({}));
          throw new Error(errBody.detail || `Request failed (${res.status})`);
        }

        const data = await res.json();
        setResult(data);
        setRefreshKey((k) => k + 1);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : t.common.error);
      } finally {
        setLoading(false);
      }
    },
    [t.common.error],
  );

  const handleCompare = async () => {
    setComparing(true);
    setCompareError(null);
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
      const body: Record<string, unknown> = {
        user_work_description: lastDescription,
        image_description: lastImage?.image_description || null,
      };
      if (lastJudgment) {
        body.user_judgment = {
          score: lastJudgment.score,
          strengths: lastJudgment.strengths.length > 0 ? lastJudgment.strengths : null,
          weaknesses: lastJudgment.weaknesses.length > 0 ? lastJudgment.weaknesses : null,
          priority_fixes: lastJudgment.priority_fixes.length > 0 ? lastJudgment.priority_fixes : null,
          target_audience: lastJudgment.target_audience || null,
          price_band: lastJudgment.price_band || null,
        };
      }

      const res = await fetch(`${base}/compare-with-references`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Compare failed");
      }

      const data = await res.json();
      setCompareResult(data);
    } catch (err: unknown) {
      setCompareError(err instanceof Error ? err.message : "Compare failed");
    } finally {
      setComparing(false);
    }
  };

  return (
    <div className="space-y-8">
      <TaskForm onSubmit={handleSubmit} loading={loading} />

      {error && (
        <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && (
        <div className="text-center text-sm text-gray-500">{t.common.loading}</div>
      )}

      {result && taskType && (
        <>
          <ResultCard data={result} taskType={taskType} />

          {/* V1.4: Compare with References button */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleCompare}
              disabled={comparing}
              className={`rounded px-4 py-2 text-sm font-medium text-white transition ${
                comparing
                  ? "cursor-not-allowed bg-gray-300"
                  : "bg-teal-600 hover:bg-teal-700"
              }`}
            >
              {comparing ? "Comparing..." : "Compare with References"}
            </button>
          </div>

          {compareError && (
            <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {compareError}
            </div>
          )}

          {compareResult && <CompareResultCard data={compareResult} />}
        </>
      )}

      <ReferencePanel />
      <SessionList refreshKey={refreshKey} />
    </div>
  );
}

/** Displays the compare-with-references result. */
function CompareResultCard({ data }: { data: Record<string, unknown> }) {
  return (
    <section className="rounded border border-teal-200 bg-teal-50 p-4">
      <h3 className="mb-3 text-sm font-semibold text-teal-800">
        Reference Comparison
      </h3>

      {(data.overall_level_estimate as string) && (
        <p className="mb-2 text-sm">
          <b>Your level estimate:</b>{" "}
          <span className={`rounded px-2 py-0.5 text-xs font-medium ${
            String(data.overall_level_estimate) === "high"
              ? "bg-green-100 text-green-700"
              : String(data.overall_level_estimate) === "medium"
              ? "bg-amber-100 text-amber-700"
              : "bg-red-100 text-red-700"
          }`}>
            {String(data.overall_level_estimate)}
          </span>
        </p>
      )}

      {(data.training_takeaway as string) && (
        <p className="mb-3 text-sm text-teal-700">{String(data.training_takeaway)}</p>
      )}

      {["weaker_than_high_cases", "key_gaps", "priority_fixes", "next_practice"].map((field) => {
        const value = data[field];
        if (!Array.isArray(value) || value.length === 0) return null;
        const labels: Record<string, string> = {
          weaker_than_high_cases: "Gaps vs. High References",
          key_gaps: "Key Gaps",
          priority_fixes: "Priority Fixes",
          next_practice: "Next Practice",
        };
        return (
          <div key={field} className="mb-2">
            <h4 className="mb-1 text-xs font-semibold text-teal-600">{labels[field] ?? field}</h4>
            <ul className="list-inside list-disc space-y-0.5">
              {value.map((item: unknown, i: number) => (
                <li key={i} className="text-sm text-teal-800">{String(item)}</li>
              ))}
            </ul>
          </div>
        );
      })}
    </section>
  );
}
