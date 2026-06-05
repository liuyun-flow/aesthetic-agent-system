"use client";

import { useState, useCallback } from "react";
import TaskForm, { type UserJudgment, type ImageData } from "@/components/TaskForm";
import ResultCard from "@/components/ResultCard";
import SessionList from "@/components/SessionList";
import { useT } from "@/i18n";

type TaskType = "analyze" | "critique" | "iterate";

export default function Home() {
  const { t } = useT();
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [taskType, setTaskType] = useState<TaskType | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleSubmit = useCallback(
    async (description: string, type: TaskType, judgment: UserJudgment | null, image: ImageData | null) => {
      setLoading(true);
      setError(null);
      setResult(null);
      setTaskType(type);

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

      {result && taskType && <ResultCard data={result} taskType={taskType} />}

      <SessionList refreshKey={refreshKey} />
    </div>
  );
}
