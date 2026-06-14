"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import Link from "next/link";
import TaskForm, { type UserJudgment, type ImageData } from "@/components/TaskForm";
import ResultCard, { type DirectionData } from "@/components/ResultCard";
import SessionList from "@/components/SessionList";
import ReferencePanel, { type CaseDraft } from "@/components/ReferencePanel";
import TrainingPanel from "@/components/TrainingPanel";
import { useT } from "@/i18n";

type TaskType = "analyze" | "critique" | "iterate";

export default function Home() {
  const { t } = useT();
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [taskType, setTaskType] = useState<TaskType | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [canceled, setCanceled] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const abortRef = useRef<AbortController | null>(null);
  const resultRef = useRef<HTMLDivElement | null>(null);

  // Bring the fresh result into view — it renders below the long form.
  useEffect(() => {
    if (result && resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [result]);

  // V1.4 compare
  const [comparing, setComparing] = useState(false);
  const [compareResult, setCompareResult] = useState<Record<string, unknown> | null>(null);
  const [compareError, setCompareError] = useState<string | null>(null);

  // V1.4.1 prompt generator
  const [generatingPrompt, setGeneratingPrompt] = useState(false);
  const [promptResult, setPromptResult] = useState<Record<string, unknown> | null>(null);
  const [promptError, setPromptError] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [lastSessionId, setLastSessionId] = useState<number | null>(null);

  // V1.7.2: Iteration direction selection + direction-based prompt generation
  const [selectedDirection, setSelectedDirection] = useState<DirectionData | null>(null);
  const [generatingDirectionPrompt, setGeneratingDirectionPrompt] = useState(false);
  const [directionPromptResult, setDirectionPromptResult] = useState<Record<string, unknown> | null>(null);
  const [directionPromptError, setDirectionPromptError] = useState<string | null>(null);
  const [directionPromptCopiedKey, setDirectionPromptCopiedKey] = useState<string | null>(null);

  // Stash last submission for compare + prompt
  const [lastDescription, setLastDescription] = useState("");
  const [lastJudgment, setLastJudgment] = useState<UserJudgment | null>(null);
  const [lastImage, setLastImage] = useState<ImageData | null>(null);
  const [lastType, setLastType] = useState<TaskType | null>(null);

  // V1.7.1: Config status bar
  const [sysStatus, setSysStatus] = useState<Record<string, unknown> | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);

  // Re-practice a past session: prefill the form from history
  const [prefill, setPrefill] = useState<{ description: string; taskType: TaskType; key: number } | null>(null);

  const handleRetrain = useCallback((description: string, recordType: string) => {
    const type: TaskType =
      recordType === "critique" || recordType === "iterate" ? recordType : "analyze";
    setPrefill({ description, taskType: type, key: Date.now() });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  // V2.3: one-click 收入案例库 — fetch a draft from a session and prefill the case form
  const [casePrefill, setCasePrefill] = useState<{ draft: CaseDraft; imageUrl: string | null; key: number } | null>(null);
  const [refOpenSignal, setRefOpenSignal] = useState(0);
  const [addingToLibrary, setAddingToLibrary] = useState(false);
  const [addLibraryError, setAddLibraryError] = useState<string | null>(null);
  const refSectionRef = useRef<HTMLDivElement | null>(null);

  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

  const handleAddToLibrary = useCallback(async (sessionId: number, imageUrl: string | null) => {
    setAddingToLibrary(true);
    setAddLibraryError(null);
    try {
      const res = await fetch(`${base}/sessions/${sessionId}/case-draft`);
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || t.addToLibrary.failed); }
      const draft: CaseDraft = await res.json();
      setCasePrefill({ draft, imageUrl, key: Date.now() });
      setRefOpenSignal((k) => k + 1);
      setTimeout(() => refSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
    } catch (err: unknown) {
      setAddLibraryError(err instanceof Error ? err.message : t.addToLibrary.failed);
    } finally {
      setAddingToLibrary(false);
    }
  }, [base, t.addToLibrary.failed]);

  useEffect(() => {
    fetch(`${base}/system/status`)
      .then((r) => r.json())
      .then((d) => { setSysStatus(d); setStatusLoading(false); })
      .catch(() => setStatusLoading(false));
  }, [base]);

  const handleSubmit = useCallback(
    async (description: string, type: TaskType, judgment: UserJudgment | null, image: ImageData | null) => {
      setLoading(true); setError(null); setResult(null);
      setCanceled(false);
      setCompareResult(null); setPromptResult(null);
      setSelectedDirection(null);
      setDirectionPromptResult(null);
      setDirectionPromptError(null);
      setTaskType(type); setLastDescription(description);
      setLastJudgment(judgment); setLastImage(image); setLastType(type);

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const body: Record<string, unknown> = { work_description: description };
        if (image) { body.image_id = image.image_id; if (image.image_description) body.image_description = image.image_description; }
        if (judgment) { body.user_judgment = { score: judgment.score, strengths: judgment.strengths.length > 0 ? judgment.strengths : null, weaknesses: judgment.weaknesses.length > 0 ? judgment.weaknesses : null, priority_fixes: judgment.priority_fixes.length > 0 ? judgment.priority_fixes : null, target_audience: judgment.target_audience || null, price_band: judgment.price_band || null }; }

        const res = await fetch(`${base}/${type}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal: controller.signal });
        if (!res.ok) { const errBody = await res.json().catch(() => ({})); throw new Error(errBody.detail || `Request failed (${res.status})`); }
        const data = await res.json();
        setResult(data);
        setRefreshKey((k) => k + 1);
        // Track latest session ID for training completion
        fetch(`${base}/sessions?limit=1`).then(r => r.json()).then(d => {
          if (d.sessions?.length > 0) setLastSessionId(d.sessions[0].id);
        }).catch(() => {});
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") { setCanceled(true); }
        else { setError(err instanceof Error ? err.message : t.common.error); }
      }
      finally { setLoading(false); }
    }, [t.common.error, base], // eslint-disable-line react-hooks/exhaustive-deps
  );

  const handleCompare = async () => {
    setComparing(true); setCompareError(null);
    try {
      const body: Record<string, unknown> = { user_work_description: lastDescription, image_description: lastImage?.image_description || null };
      if (lastJudgment) { body.user_judgment = { score: lastJudgment.score, strengths: lastJudgment.strengths.length > 0 ? lastJudgment.strengths : null, weaknesses: lastJudgment.weaknesses.length > 0 ? lastJudgment.weaknesses : null, priority_fixes: lastJudgment.priority_fixes.length > 0 ? lastJudgment.priority_fixes : null, target_audience: lastJudgment.target_audience || null, price_band: lastJudgment.price_band || null }; }
      const res = await fetch(`${base}/compare-with-references`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || t.common.compareFailed); }
      setCompareResult(await res.json());
    } catch (err: unknown) { setCompareError(err instanceof Error ? err.message : t.common.compareFailed); }
    finally { setComparing(false); }
  };

  const handleGeneratePrompt = async () => {
    setGeneratingPrompt(true); setPromptError(null);
    try {
      const body: Record<string, unknown> = {
        work_description: lastDescription,
        image_description: lastImage?.image_description || null,
        target_tool: "general",
      };
      if (lastJudgment) { body.user_judgment = { score: lastJudgment.score, strengths: lastJudgment.strengths.length > 0 ? lastJudgment.strengths : null, weaknesses: lastJudgment.weaknesses.length > 0 ? lastJudgment.weaknesses : null, priority_fixes: lastJudgment.priority_fixes.length > 0 ? lastJudgment.priority_fixes : null, target_audience: lastJudgment.target_audience || null, price_band: lastJudgment.price_band || null }; }
      if (result) { body.critique_result = result; body.iterate_result = result; }
      if (compareResult) { body.reference_comparison = compareResult; }
      const res = await fetch(`${base}/generate-prompt`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || t.common.generateFailed); }
      setPromptResult(await res.json());
    } catch (err: unknown) { setPromptError(err instanceof Error ? err.message : t.common.generateFailed); }
    finally { setGeneratingPrompt(false); }
  };

  const handleCopy = async (text: string, key: string) => {
    try { await navigator.clipboard.writeText(text); setCopiedKey(key); setTimeout(() => setCopiedKey(null), 2000); }
    catch { /* ignore */ }
  };

  // V1.7.2: Direction selection & prompt generation
  const handleSelectDirection = (direction: DirectionData) => {
    setSelectedDirection(direction);
    setDirectionPromptResult(null);
    setDirectionPromptError(null);
  };

  const handleGenerateDirectionPrompt = async (direction: DirectionData) => {
    setGeneratingDirectionPrompt(true);
    setDirectionPromptError(null);
    setDirectionPromptResult(null);
    try {
      const body: Record<string, unknown> = {
        work_description: lastDescription,
        image_description: lastImage?.image_description || null,
        target_tool: "general",
        selected_direction: JSON.stringify(direction, null, 2),
      };
      if (lastSessionId) {
        body.session_id = lastSessionId;
      }
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
      if (result) {
        body.iterate_result = result;
      }
      if (compareResult) {
        body.reference_comparison = compareResult;
      }
      const res = await fetch(`${base}/generate-prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || t.common.generateFailed);
      }
      setDirectionPromptResult(await res.json());
    } catch (err: unknown) {
      setDirectionPromptError(err instanceof Error ? err.message : t.common.generateFailed);
    } finally {
      setGeneratingDirectionPrompt(false);
    }
  };

  const handleDirectionPromptCopy = async (text: string, key: string) => {
    try { await navigator.clipboard.writeText(text); setDirectionPromptCopiedKey(key); setTimeout(() => setDirectionPromptCopiedKey(null), 2000); }
    catch { /* ignore */ }
  };

  return (
    <div className="space-y-8">
      {/* V1.7.1: Config status bar */}
      <ConfigStatusBar
        sysStatus={sysStatus}
        loading={statusLoading}
        t={t}
      />

      <TaskForm onSubmit={handleSubmit} loading={loading} prefill={prefill} />

      {error && <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
      {canceled && !loading && <div className="rounded border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-500">{t.progress.canceled}</div>}
      {loading && taskType && (
        <AgentProgress
          taskType={taskType}
          t={t}
          onCancel={() => abortRef.current?.abort()}
        />
      )}

      {result && taskType && (
        <div ref={resultRef} className="space-y-4 scroll-mt-4">
          <ResultCard
            data={result}
            taskType={taskType}
            selectedDirectionId={selectedDirection?.id ?? null}
            onSelectDirection={handleSelectDirection}
            onGeneratePrompt={handleGenerateDirectionPrompt}
            generatingPrompt={generatingDirectionPrompt}
          />

          {/* V1.4 Compare */}
          <button onClick={handleCompare} disabled={comparing}
            className={`rounded px-4 py-2 text-sm font-medium text-white transition ${comparing ? "cursor-not-allowed bg-gray-300" : "bg-teal-600 hover:bg-teal-700"}`}>
            {comparing ? t.result.comparing : t.result.compareWithRefs}
          </button>

          {/* V2.3 One-click add to case library */}
          {lastSessionId && (
            <button onClick={() => handleAddToLibrary(lastSessionId, null)} disabled={addingToLibrary}
              title={t.addToLibrary.hint}
              className={`ml-2 rounded px-4 py-2 text-sm font-medium text-white transition ${addingToLibrary ? "cursor-not-allowed bg-gray-300" : "bg-rose-600 hover:bg-rose-700"}`}>
              {addingToLibrary ? t.addToLibrary.loading : t.addToLibrary.button}
            </button>
          )}
          {addLibraryError && <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{addLibraryError}</div>}
          {compareError && <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{compareError}</div>}
          {compareResult && <CompareResultCard data={compareResult} t={t} />}

          {/* V1.7.2 Direction-based prompt result */}
          {directionPromptError && <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{directionPromptError}</div>}
          {directionPromptResult && selectedDirection && (
            <DirectionPromptResultCard
              data={directionPromptResult}
              direction={selectedDirection}
              t={t}
              copiedKey={directionPromptCopiedKey}
              onCopy={handleDirectionPromptCopy}
            />
          )}

          {/* V1.4.1 Generate Prompt — for iterate the per-direction flow above is the primary path */}
          {taskType !== "iterate" && (
            <>
              <button onClick={handleGeneratePrompt} disabled={generatingPrompt}
                className={`rounded px-4 py-2 text-sm font-medium text-white transition ml-2 ${generatingPrompt ? "cursor-not-allowed bg-gray-300" : "bg-indigo-600 hover:bg-indigo-700"}`}>
                {generatingPrompt ? t.result.generatingPrompt : t.result.generatePrompt}
              </button>
              {promptError && <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{promptError}</div>}
              {promptResult && <PromptResultCard data={promptResult} t={t} copiedKey={copiedKey} onCopy={handleCopy} />}
            </>
          )}
        </div>
      )}

      <CollapsibleSection id="training" title={t.sections.training} defaultOpen t={t}>
        <TrainingPanel refreshKey={refreshKey} lastSessionId={lastSessionId} />
      </CollapsibleSection>
      <div ref={refSectionRef} className="scroll-mt-4">
        <CollapsibleSection id="reference" title={t.reference.title} defaultOpen={false} t={t} forceOpen={refOpenSignal}>
          <ReferencePanel prefill={casePrefill} />
        </CollapsibleSection>
      </div>
      <CollapsibleSection id="sessions" title={t.sessions.recentSessions} defaultOpen t={t}>
        <SessionList refreshKey={refreshKey} onRetrain={handleRetrain} onAddToLibrary={handleAddToLibrary} />
      </CollapsibleSection>
    </div>
  );
}

/* ── Collapsible workbench section ───────────────────────────────── */

function CollapsibleSection({
  id,
  title,
  defaultOpen,
  t,
  children,
  forceOpen,
}: {
  id: string;
  title: string;
  defaultOpen?: boolean;
  t: ReturnType<typeof useT>["t"];
  children: React.ReactNode;
  /** When this number changes (and is >0), force the section open. */
  forceOpen?: number;
}) {
  const [open, setOpen] = useState(defaultOpen ?? true);

  // Restore the user's last choice after mount (avoids SSR hydration mismatch).
  useEffect(() => {
    const saved = localStorage.getItem(`workbench-section-${id}`);
    if (saved !== null) setOpen(saved === "1");
  }, [id]);

  // Force open on external signal (e.g. one-click 收入案例库 targeting this section).
  useEffect(() => {
    if (forceOpen && forceOpen > 0) setOpen(true);
  }, [forceOpen]);

  const toggle = () => {
    setOpen((o) => {
      localStorage.setItem(`workbench-section-${id}`, o ? "0" : "1");
      return !o;
    });
  };

  return (
    <section>
      <button
        type="button"
        onClick={toggle}
        className="mb-2 flex w-full items-center justify-between rounded border bg-white px-4 py-2.5 shadow-sm hover:bg-gray-50 transition"
      >
        <span className="text-base font-semibold text-gray-800">{title}</span>
        <span className="text-xs text-gray-400">
          {open ? `${t.sections.collapse} ▾` : `${t.sections.expand} ▸`}
        </span>
      </button>
      {open && children}
    </section>
  );
}

/* ── Staged progress while waiting for AI ────────────────────────── */

function AgentProgress({
  taskType,
  t,
  onCancel,
}: {
  taskType: TaskType;
  t: ReturnType<typeof useT>["t"];
  onCancel: () => void;
}) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, []);

  const stages = t.progress.stages[taskType];
  // Advance one stage every 6s and hold on the last; this is paced status,
  // not real model progress (the API gives none).
  const idx = Math.min(Math.floor(elapsed / 6), stages.length - 1);

  return (
    <div className="rounded border border-blue-200 bg-blue-50 px-4 py-3">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm text-blue-700">
          <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
          <span>{stages[idx]}</span>
        </div>
        <button
          onClick={onCancel}
          className="rounded border border-blue-300 px-3 py-1 text-xs text-blue-600 hover:bg-blue-100 transition"
        >
          {t.progress.cancel}
        </button>
      </div>
      <div className="mt-1.5 flex items-center justify-between text-xs text-blue-400">
        <span>{t.progress.hint}</span>
        <span>{t.progress.elapsed} {elapsed}{t.progress.seconds}</span>
      </div>
      <div className="mt-2 flex gap-1">
        {stages.map((_, i) => (
          <span
            key={i}
            className={`h-1 flex-1 rounded-full transition ${
              i <= idx ? "bg-blue-400" : "bg-blue-100"
            }`}
          />
        ))}
      </div>
    </div>
  );
}

function CompareResultCard({ data, t }: { data: Record<string, unknown>; t: ReturnType<typeof useT>["t"] }) {
  return (
    <section className="rounded border border-teal-200 bg-teal-50 p-4">
      <h3 className="mb-3 text-sm font-semibold text-teal-800">{t.result.refComparison}</h3>
      {(data.overall_level_estimate as string) && (
        <p className="mb-2 text-sm">
          <b>{t.result.yourLevel}:</b>{" "}
          <span className={`rounded px-2 py-0.5 text-xs font-medium ${String(data.overall_level_estimate) === "high" ? "bg-green-100 text-green-700" : String(data.overall_level_estimate) === "medium" ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"}`}>
            {String(data.overall_level_estimate) === "high" ? t.reference.high : String(data.overall_level_estimate) === "medium" ? t.reference.medium : t.reference.low}
          </span>
        </p>
      )}
      {(data.training_takeaway as string) && <p className="mb-3 text-sm text-teal-700">{String(data.training_takeaway)}</p>}
      {(["weaker_than_high_cases", "key_gaps", "priority_fixes", "next_practice"] as const).map((field) => {
        const value = data[field];
        if (!Array.isArray(value) || value.length === 0) return null;
        const labels: Record<string, string> = { weaker_than_high_cases: t.result.gapsVsHigh, key_gaps: t.result.keyGaps, priority_fixes: t.result.priorityFixes, next_practice: t.result.nextPractice };
        return (
          <div key={field} className="mb-2">
            <h4 className="mb-1 text-xs font-semibold text-teal-600">{labels[field]}</h4>
            <ul className="list-inside list-disc space-y-0.5">{value.map((item: unknown, i: number) => (<li key={i} className="text-sm text-teal-800">{String(item)}</li>))}</ul>
          </div>
        );
      })}
    </section>
  );
}

/* ── V1.7.1 Config Status Bar ─────────────────────────────────────── */

function ConfigStatusBar({
  sysStatus,
  loading,
  t,
}: {
  sysStatus: Record<string, unknown> | null;
  loading: boolean;
  t: ReturnType<typeof useT>["t"];
}) {
  if (loading) {
    return (
      <div className="rounded border bg-gray-50 px-4 py-2 text-xs text-gray-400">
        {t.status.loading}
      </div>
    );
  }

  if (!sysStatus) {
    return (
      <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-600 flex items-center justify-between">
        <span>{t.status.loading} — {t.common.loadError}</span>
        <Link href="/help" className="underline">{t.status.viewHelp}</Link>
      </div>
    );
  }

  const ds = sysStatus.deepseek as Record<string, unknown> | undefined;
  const vis = sysStatus.vision as Record<string, unknown> | undefined;
  const dbOk = sysStatus.database === "ok";
  const uploadsOk = sysStatus.uploads === "ok";
  const allOk = ds?.configured && vis?.configured && dbOk && uploadsOk;

  const items = [
    {
      label: t.status.deepseek,
      ok: !!ds?.configured,
      detail: ds?.configured ? t.status.configured : t.status.notConfigured,
    },
    {
      label: t.status.vision,
      ok: !!vis?.configured,
      detail: vis?.configured
        ? t.status.configured
        : vis?.is_placeholder
        ? t.status.placeholder
        : t.status.notConfigured,
    },
    { label: t.status.database, ok: dbOk, detail: dbOk ? t.status.normal : t.status.error },
    { label: t.status.uploads, ok: uploadsOk, detail: uploadsOk ? t.status.normal : t.status.error },
  ];

  return (
    <div
      className={`rounded border px-4 py-2.5 ${
        allOk
          ? "border-green-200 bg-green-50"
          : "border-amber-200 bg-amber-50"
      }`}
    >
      <div className="flex items-center flex-wrap gap-x-4 gap-y-1">
        <span className="text-xs font-medium text-gray-500 mr-1">{t.status.title}:</span>
        {items.map((item) => (
          <span
            key={item.label}
            className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium ${
              item.ok
                ? "bg-green-100 text-green-700"
                : "bg-red-100 text-red-700"
            }`}
          >
            <span
              className={`inline-block w-1.5 h-1.5 rounded-full ${
                item.ok ? "bg-green-500" : "bg-red-500"
              }`}
            />
            {item.label}: {item.detail}
          </span>
        ))}
        {!allOk && (
          <span className="inline-flex items-center gap-2 ml-auto">
            <Link
              href="/settings"
              className="text-xs text-blue-600 hover:underline font-medium"
            >
              {t.status.goSettings}
            </Link>
            <Link
              href="/help"
              className="text-xs text-blue-600 hover:underline font-medium"
            >
              {t.status.viewHelp}
            </Link>
          </span>
        )}
      </div>
    </div>
  );
}

/* ── V1.7.2 Direction-based Prompt Result ────────────────────────── */

function DirectionPromptResultCard({
  data,
  direction,
  t,
  copiedKey,
  onCopy,
}: {
  data: Record<string, unknown>;
  direction: DirectionData;
  t: ReturnType<typeof useT>["t"];
  copiedKey: string | null;
  onCopy: (text: string, key: string) => void;
}) {
  const fields: [string, string][] = [
    ["chinese_prompt", t.result.chinesePrompt],
    ["english_prompt", t.result.englishPrompt],
    ["negative_prompt", t.result.negativePrompt],
    ["design_notes", t.result.designNotes],
    ["copywriting_prompt", t.result.copywritingPrompt],
    ["usage_tips", t.result.usageTips],
  ];

  return (
    <section className="rounded border border-indigo-300 bg-indigo-50/50 p-4">
      <div className="mb-3 flex items-center gap-2">
        <span className="text-sm font-semibold text-indigo-800">
          基于「{direction.title}」生成的提示词
        </span>
        <span className="rounded bg-indigo-100 px-2 py-0.5 text-xs text-indigo-600">
          {direction.id}
        </span>
      </div>
      <div className="space-y-3">
        {fields.map(([key, label]) => {
          const value = data[key];
          if (!value || (Array.isArray(value) && value.length === 0)) return null;
          const text = Array.isArray(value) ? value.join("\n") : String(value);
          return (
            <div key={key}>
              <div className="flex items-center justify-between mb-1">
                <h4 className="text-xs font-semibold text-indigo-600">{label}</h4>
                <button
                  onClick={() => onCopy(text, `dir-${key}`)}
                  className="rounded border border-indigo-300 px-2 py-0.5 text-xs text-indigo-600 hover:bg-indigo-100"
                >
                  {copiedKey === `dir-${key}` ? t.result.copied : t.result.copy}
                </button>
              </div>
              <pre className="whitespace-pre-wrap rounded bg-white p-2 text-xs text-gray-700 border border-indigo-100">
                {text}
              </pre>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function PromptResultCard({ data, t, copiedKey, onCopy }: { data: Record<string, unknown>; t: ReturnType<typeof useT>["t"]; copiedKey: string | null; onCopy: (text: string, key: string) => void }) {
  const fields: [string, string][] = [
    ["chinese_prompt", t.result.chinesePrompt],
    ["english_prompt", t.result.englishPrompt],
    ["negative_prompt", t.result.negativePrompt],
    ["design_notes", t.result.designNotes],
    ["copywriting_prompt", t.result.copywritingPrompt],
    ["usage_tips", t.result.usageTips],
  ];

  return (
    <section className="rounded border border-indigo-200 bg-indigo-50 p-4">
      <h3 className="mb-3 text-sm font-semibold text-indigo-800">{t.result.generatePrompt}</h3>
      <div className="space-y-3">
        {fields.map(([key, label]) => {
          const value = data[key];
          if (!value || (Array.isArray(value) && value.length === 0)) return null;
          const text = Array.isArray(value) ? value.join("\n") : String(value);
          return (
            <div key={key}>
              <div className="flex items-center justify-between mb-1">
                <h4 className="text-xs font-semibold text-indigo-600">{label}</h4>
                <button onClick={() => onCopy(text, key)}
                  className="rounded border border-indigo-300 px-2 py-0.5 text-xs text-indigo-600 hover:bg-indigo-100">
                  {copiedKey === key ? t.result.copied : t.result.copy}
                </button>
              </div>
              <pre className="whitespace-pre-wrap rounded bg-white p-2 text-xs text-gray-700 border border-indigo-100">{text}</pre>
            </div>
          );
        })}
      </div>
    </section>
  );
}
