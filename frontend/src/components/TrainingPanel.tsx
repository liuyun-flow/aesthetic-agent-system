"use client";

import { useState, useEffect } from "react";
import { useT } from "@/i18n";

interface Props {
  refreshKey: number;
  lastSessionId: number | null;
}

export default function TrainingPanel({ refreshKey, lastSessionId }: Props) {
  const { t } = useT();
  const [today, setToday] = useState<Record<string, unknown> | null>(null);
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);
  const [review, setReview] = useState<Record<string, unknown> | null>(null);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [completeError, setCompleteError] = useState<string | null>(null);
  const [completeSaved, setCompleteSaved] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [lesson, setLesson] = useState("");
  const [nextFocus, setNextFocus] = useState("");
  const [afterScore, setAfterScore] = useState("");

  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

  useEffect(() => {
    fetch(`${base}/training/today`).then(r => r.json()).then(setToday).catch(() => {});
    fetch(`${base}/training/stats`).then(r => r.json()).then(setStats).catch(() => {});
  }, [refreshKey, base]);

  const handleComplete = async () => {
    if (!lastSessionId) return;
    setCompleting(true);
    setCompleteError(null);
    setCompleteSaved(false);
    try {
      const res = await fetch(`${base}/training/sessions/${lastSessionId}/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          training_theme: today?.theme ? String(today.theme) : null,
          user_lesson: lesson.trim() || null,
          next_focus: nextFocus.trim() || null,
          after_score: afterScore ? parseInt(afterScore, 10) : null,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "保存失败，请稍后重试");
      }
      // Only clear the form after a confirmed save.
      setLesson(""); setNextFocus(""); setAfterScore("");
      setCompleteSaved(true);
      setTimeout(() => setCompleteSaved(false), 3000);
      fetch(`${base}/training/stats`).then(r => r.json()).then(setStats).catch(() => {});
    } catch (err: unknown) {
      setCompleteError(err instanceof Error ? err.message : "保存失败，请稍后重试");
    }
    finally { setCompleting(false); }
  };

  const handleWeeklyReview = async () => {
    setReviewLoading(true);
    setReviewError(null);
    try {
      const res = await fetch(`${base}/training/weekly-review`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "生成复盘失败，请稍后重试");
      }
      setReview(await res.json());
    } catch (err: unknown) {
      setReviewError(err instanceof Error ? err.message : "生成复盘失败，请稍后重试");
    }
    finally { setReviewLoading(false); }
  };

  return (
    <section className="space-y-4">
      {/* Today's training */}
      <div className="rounded border bg-white p-4 shadow-sm">
        <h2 className="mb-3 text-base font-semibold text-gray-800">今日训练</h2>
        {today ? (
          <>
            <p className="mb-2 text-sm">
              主题：<span className="font-semibold text-blue-700">{String(today.theme)}</span>
            </p>
            <ul className="list-inside list-disc space-y-1 text-sm text-gray-600">
              {(today.tasks as string[])?.map((task, i) => (
                <li key={i}>{task}</li>
              ))}
            </ul>
          </>
        ) : (
          <p className="text-xs text-gray-400">加载中…</p>
        )}
      </div>

      {/* Stats */}
      {stats && (
        <div className="rounded border bg-white p-4 shadow-sm">
          <h2 className="mb-2 text-base font-semibold text-gray-800">训练统计</h2>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <Stat label="总次数" value={String(stats.total_sessions ?? 0)} />
            <Stat label="已完成" value={String(stats.completed_sessions ?? 0)} />
            <Stat label="本周" value={String(stats.sessions_this_week ?? 0)} />
            <Stat label="连续天数" value={String(stats.current_streak_days ?? 0)} />
            <Stat label="平均自评" value={stats.average_user_score != null ? String(stats.average_user_score) : "-"} />
            <Stat label="平均 AI" value={stats.average_ai_score != null ? String(stats.average_ai_score) : "-"} />
          </div>
        </div>
      )}

      {/* Complete training form */}
      {lastSessionId && (
        <div className="rounded border bg-white p-4 shadow-sm">
          <h2 className="mb-2 text-base font-semibold text-gray-800">完成训练记录</h2>
          <textarea rows={2} value={lesson} onChange={(e) => setLesson(e.target.value)}
            placeholder="今天学到的一条审美规则…"
            className="w-full rounded border px-2 py-1 text-sm mb-2" />
          <input value={nextFocus} onChange={(e) => setNextFocus(e.target.value)}
            placeholder="下次重点注意什么…"
            className="w-full rounded border px-2 py-1 text-sm mb-2" />
          <div className="flex gap-2 items-center mb-2">
            <input type="number" min={0} max={100} value={afterScore}
              onChange={(e) => setAfterScore(e.target.value)}
              placeholder="修改后评分" className="w-28 rounded border px-2 py-1 text-sm" />
            <button onClick={handleComplete} disabled={completing}
              className="rounded bg-green-600 px-4 py-1 text-xs text-white hover:bg-green-700 disabled:bg-gray-300">
              {completing ? "保存中…" : "标记完成"}
            </button>
            {completeSaved && <span className="text-xs text-green-600">已保存 ✓</span>}
          </div>
          {completeError && (
            <p className="text-xs text-red-500">{completeError}</p>
          )}
        </div>
      )}

      {/* Weekly review button */}
      <button onClick={handleWeeklyReview} disabled={reviewLoading}
        className="rounded bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:bg-gray-300">
        {reviewLoading ? "生成中…" : "生成本周复盘"}
      </button>
      {reviewError && (
        <p className="text-xs text-red-500">{reviewError}</p>
      )}

      {review && (
        <div className="rounded border bg-indigo-50 p-4">
          <h3 className="mb-2 text-sm font-semibold text-indigo-800">本周复盘</h3>
          {(["summary", "common_misjudgments", "progress_points", "recurring_issues"] as const).map((k) => (
            (review[k] as string) && <p key={k} className="mb-2 text-sm text-indigo-700">{String(review[k])}</p>
          ))}
          {(review.next_week_theme as string) && (
            <p className="text-sm"><b>下周主题：</b>{String(review.next_week_theme)}</p>
          )}
          {Array.isArray(review.next_week_tasks) && (review.next_week_tasks as string[]).length > 0 && (
            <ul className="list-inside list-disc mt-1 text-sm text-indigo-700">
              {(review.next_week_tasks as string[]).map((t, i) => <li key={i}>{t}</li>)}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded bg-gray-50 px-2 py-1 text-center">
      <div className="text-gray-500">{label}</div>
      <div className="font-semibold text-gray-800">{value}</div>
    </div>
  );
}
