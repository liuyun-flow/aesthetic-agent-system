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
}

interface Props {
  refreshKey: number;
}

export default function SessionList({ refreshKey }: Props) {
  const { t } = useT();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchSessions() {
      setLoading(true);
      setError(null);
      try {
        const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
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
  }, [refreshKey]);

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
    <section>
      <h2 className="mb-3 text-base font-semibold text-gray-800">{t.sessions.recentSessions}</h2>
      <div className="space-y-2">
        {sessions.map((s) => (
          <div key={s.id} className="flex items-start gap-3 rounded border bg-white px-3 py-2 text-sm">
            <span className={`mt-0.5 rounded px-1.5 py-0.5 text-xs font-medium ${
              s.record_type === "analyze" ? "bg-purple-100 text-purple-700"
              : s.record_type === "critique" ? "bg-amber-100 text-amber-700"
              : "bg-emerald-100 text-emerald-700"
            }`}>
              {t.tasks[s.record_type as keyof typeof t.tasks]?.label ?? s.record_type}
            </span>
            <span className="flex-1 truncate text-gray-600">{s.work_description}</span>
            {s.judgment_gap_summary && (
              <span className="text-xs text-purple-500" title={s.judgment_gap_summary}>⚡</span>
            )}
            <span className="text-xs text-gray-400">
              {new Date(s.created_at).toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
