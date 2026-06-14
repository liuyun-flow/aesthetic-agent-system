"use client";

import { useState, useRef, useEffect, useCallback, type FormEvent } from "react";
import { useT } from "@/i18n";

type TaskType = "analyze" | "critique" | "iterate";

export interface UserJudgment {
  score: number | null;
  strengths: string[];
  weaknesses: string[];
  priority_fixes: string[];
  target_audience: string;
  price_band: string;
}

export interface ImageData {
  image_id: number;
  image_description: string;
}

interface Props {
  onSubmit: (
    description: string,
    type: TaskType,
    judgment: UserJudgment | null,
    image: ImageData | null,
  ) => void;
  loading: boolean;
  /** Set from history "再练一次" — key changes on every request so the same session can be reloaded twice. */
  prefill?: { description: string; taskType: TaskType; key: number } | null;
}

const TASK_KEYS = ["analyze", "critique", "iterate"] as const;

export default function TaskForm({ onSubmit, loading, prefill }: Props) {
  const { t } = useT();
  const [description, setDescription] = useState("");
  const [taskType, setTaskType] = useState<TaskType>("analyze");
  const [prefillNotice, setPrefillNotice] = useState(false);

  // Load a past session's description for re-practice
  useEffect(() => {
    if (!prefill) return;
    setDescription(prefill.description);
    setTaskType(prefill.taskType);
    setPrefillNotice(true);
    const timer = setTimeout(() => setPrefillNotice(false), 6000);
    return () => clearTimeout(timer);
  }, [prefill]);
  // V2.3: guided context fields (merged into the description on submit)
  const [gCategory, setGCategory] = useState("");
  const [gAudience, setGAudience] = useState("");
  const [gPriceBand, setGPriceBand] = useState("");
  const [gUseCase, setGUseCase] = useState("");

  const [showJudgment, setShowJudgment] = useState(false);
  const [judgeScore, setJudgeScore] = useState("");
  const [judgeStrengths, setJudgeStrengths] = useState("");
  const [judgeWeaknesses, setJudgeWeaknesses] = useState("");
  const [judgeFixes, setJudgeFixes] = useState("");
  const [judgeAudience, setJudgeAudience] = useState("");
  const [judgePriceBand, setJudgePriceBand] = useState("");

  // V1.2 image upload
  const fileRef = useRef<HTMLInputElement>(null);
  const [imageId, setImageId] = useState<number | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [imageDesc, setImageDesc] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  // V1.3 auto-describe
  const [describing, setDescribing] = useState(false);
  const [describeError, setDescribeError] = useState<string | null>(null);
  const [visionSummary, setVisionSummary] = useState<Record<string, unknown> | null>(null);
  // V1.4.3 vision status
  const [visionStatus, setVisionStatus] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
    fetch(`${base}/vision/status`)
      .then((r) => r.json())
      .then((d) => setVisionStatus(d))
      .catch(() => setVisionStatus(null));
  }, []);

  const describeImage = useCallback(async (id: number) => {
    setDescribing(true);
    setDescribeError(null);
    setVisionSummary(null);
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${base}/images/${id}/describe`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || t.common.describeFailed);
      }
      const data = await res.json();
      // Show warning if placeholder
      if (data.is_placeholder || data.warning) {
        setDescribeError(data.warning || "当前为占位描述，不是真实图片识别结果。");
      }
      setVisionSummary(data.description);
      if (data.description?.suggested_prompt_text) {
        setImageDesc(data.description.suggested_prompt_text);
      }
    } catch (err: unknown) {
      setDescribeError(err instanceof Error ? err.message : t.common.describeFailed);
    } finally {
      setDescribing(false);
    }
  }, [t.common.describeFailed]);

  const uploadFile = useCallback(async (file: File) => {
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      setUploadError(t.form.invalidImageType);
      return;
    }
    setUploading(true);
    setUploadError(null);
    setImageId(null);
    setImageUrl(null);
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(base + "/upload", { method: "POST", body: fd });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || t.common.uploadFailed);
      }
      const data = await res.json();
      setImageId(data.image_id);
      setImageUrl(data.url.startsWith("http") ? data.url : base + data.url);
      // Real vision is configured — describe right away, no extra click needed.
      if (visionStatus?.is_configured && !visionStatus?.is_placeholder) {
        describeImage(data.image_id);
      }
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : t.common.uploadFailed);
    } finally {
      setUploading(false);
    }
  }, [t.common.uploadFailed, t.form.invalidImageType, visionStatus, describeImage]);

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
  };

  const handleAutoDescribe = () => {
    if (imageId !== null) describeImage(imageId);
  };

  // Paste a screenshot anywhere on the page to upload it
  useEffect(() => {
    const onPaste = (e: ClipboardEvent) => {
      const files = e.clipboardData?.files;
      if (!files || files.length === 0) return;
      const file = Array.from(files).find((f) => f.type.startsWith("image/"));
      if (file) {
        e.preventDefault();
        uploadFile(file);
      }
    };
    document.addEventListener("paste", onPaste);
    return () => document.removeEventListener("paste", onPaste);
  }, [uploadFile]);

  // Drag & drop
  const [dragActive, setDragActive] = useState(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const file = Array.from(e.dataTransfer.files).find((f) => f.type.startsWith("image/"));
    if (file) uploadFile(file);
  };

  // Merge guided context fields into the description so agents receive them.
  const buildFullDescription = () => {
    const base = description.trim();
    const parts: string[] = [];
    if (gCategory.trim()) parts.push(`${t.form.fieldCategory}：${gCategory.trim()}`);
    if (gAudience.trim()) parts.push(`${t.form.fieldAudience}：${gAudience.trim()}`);
    if (gPriceBand.trim()) parts.push(`${t.form.fieldPriceBand}：${gPriceBand.trim()}`);
    if (gUseCase.trim()) parts.push(`${t.form.fieldUseCase}：${gUseCase.trim()}`);
    if (parts.length === 0) return base;
    return `${base}\n\n【补充信息】${parts.join("；")}`;
  };

  const submit = () => {
    if (description.trim().length < 10) return;

    let judgment: UserJudgment | null = null;
    if (showJudgment) {
      judgment = {
        score: judgeScore ? parseInt(judgeScore, 10) || null : null,
        strengths: judgeStrengths ? judgeStrengths.split("\n").filter(Boolean) : [],
        weaknesses: judgeWeaknesses ? judgeWeaknesses.split("\n").filter(Boolean) : [],
        priority_fixes: judgeFixes ? judgeFixes.split("\n").filter(Boolean) : [],
        target_audience: judgeAudience.trim() || "",
        price_band: judgePriceBand.trim() || "",
      };
    }

    const image: ImageData | null =
      imageId !== null
        ? { image_id: imageId, image_description: imageDesc.trim() }
        : null;

    onSubmit(buildFullDescription(), taskType, judgment, image);
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    submit();
  };

  const tooShort = description.trim().length < 10;
  const disabled = loading || tooShort;

  // V2.3: description completeness — substantive text + 4 commercial-context fields
  const completenessDims: { ok: boolean; label: string }[] = [
    { ok: description.trim().length >= 40, label: t.form.dims.colorOrComposition },
    { ok: !!gCategory.trim(), label: t.form.dims.category },
    { ok: !!gAudience.trim(), label: t.form.dims.audience },
    { ok: !!gPriceBand.trim(), label: t.form.dims.priceBand },
    { ok: !!gUseCase.trim(), label: t.form.dims.useCase },
  ];
  const filledCount = completenessDims.filter((d) => d.ok).length;
  const completenessPct = Math.round((filledCount / completenessDims.length) * 100);
  const missingLabels = completenessDims.filter((d) => !d.ok).map((d) => d.label);
  const completenessColor =
    completenessPct >= 80 ? "bg-green-500" : completenessPct >= 50 ? "bg-amber-500" : "bg-red-500";

  // Vision commercial guesses (labeled as AI 推测; never auto-applied as fact)
  const vs = visionSummary as Record<string, unknown> | null;
  const guesses: { value: string; apply: () => void }[] = [];
  if (vs) {
    const g = (k: string) => (typeof vs[k] === "string" && (vs[k] as string).trim() ? (vs[k] as string).trim() : null);
    const cat = g("design_category"); if (cat) guesses.push({ value: `${t.form.dims.category}：${cat}`, apply: () => setGCategory(cat) });
    const aud = g("target_audience_guess"); if (aud) guesses.push({ value: `${t.form.dims.audience}：${aud}`, apply: () => setGAudience(aud) });
    const pb = g("price_band_guess"); if (pb) guesses.push({ value: `${t.form.dims.priceBand}：${pb}`, apply: () => setGPriceBand(pb) });
    const uc = g("use_case"); if (uc) guesses.push({ value: `${t.form.dims.useCase}：${uc}`, apply: () => setGUseCase(uc) });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <fieldset>
        <legend className="mb-2 text-sm font-medium text-gray-600">
          {t.form.taskType}
        </legend>
        <div className="flex gap-2">
          {TASK_KEYS.map((k) => (
            <label
              key={k}
              className={`flex-1 cursor-pointer rounded border px-3 py-2 text-sm transition ${
                taskType === k
                  ? "border-blue-500 bg-blue-50 text-blue-700"
                  : "border-gray-200 bg-white hover:border-gray-300"
              }`}
            >
              <input type="radio" name="taskType" value={k} checked={taskType === k}
                onChange={() => setTaskType(k)} className="sr-only" />
              <span className="block font-medium">{t.tasks[k].label}</span>
              <span className="block text-xs text-gray-500">{t.tasks[k].desc}</span>
            </label>
          ))}
        </div>
      </fieldset>

      {/* V1.2 Image upload */}
      <div
        className={`rounded border p-3 transition ${
          dragActive ? "border-blue-400 bg-blue-50" : "bg-gray-50"
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
      >
        <p className="mb-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
          {t.form.imageSection}
          {visionStatus && (
            <span className={`ml-2 rounded px-2 py-0.5 text-xs ${
              (visionStatus.is_placeholder as boolean)
                ? "bg-amber-100 text-amber-700"
                : (visionStatus.is_configured as boolean)
                ? "bg-green-100 text-green-700"
                : "bg-red-100 text-red-700"
            }`}>
              {String(visionStatus.vision_provider ?? "?")}
              {(visionStatus.is_placeholder as boolean) ? " 占位" : (visionStatus.is_configured as boolean) ? " 已配置" : " 未配置"}
            </span>
          )}
          {visionStatus && !(visionStatus.is_configured as boolean) && !(visionStatus.is_placeholder as boolean) && (
            <p className="mt-1 text-xs text-red-500">{String(visionStatus.message ?? "")}</p>
          )}
          {visionStatus && (visionStatus.is_placeholder as boolean) && (
            <p className="mt-1 text-xs text-amber-600">
              当前为占位描述，不会真正识别图片。返回的描述是固定示例，与你的图片不匹配。
            </p>
          )}
        </p>
        <input
          ref={fileRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleUpload}
          className="text-sm"
        />
        <p className="mt-1 text-xs text-gray-400">
          {dragActive ? t.form.dropActive : t.form.dropHint}
        </p>
        {uploading && (
          <p className="mt-1 text-xs text-blue-500">{t.form.uploading}</p>
        )}
        {uploadError && (
          <p className="mt-1 text-xs text-red-500">{uploadError}</p>
        )}
        {imageUrl && (
          <div className="mt-2">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={imageUrl} alt="Preview" className="max-h-40 rounded border" />
            <div className="mt-2 flex items-center gap-2">
              <button
                type="button"
                onClick={handleAutoDescribe}
                disabled={describing}
                className={`rounded px-3 py-1 text-xs font-medium text-white transition ${
                  describing
                    ? "cursor-not-allowed bg-gray-300"
                    : "bg-purple-600 hover:bg-purple-700"
                }`}
              >
                {describing ? t.form.describing : t.form.autoDescribe}
              </button>
            </div>
            {describeError && (
              <p className="mt-1 text-xs text-red-500">{describeError}</p>
            )}
            {visionSummary && (
              <div className="mt-2 rounded border border-purple-100 bg-purple-50 p-2 text-xs">
                {Array.isArray(visionSummary.style_keywords) &&
                  visionSummary.style_keywords.length > 0 && (
                    <p className="text-purple-700">
                      <b>{t.form.visionStyle}:</b>{" "}
                      {(visionSummary.style_keywords as string[]).join(", ")}
                    </p>
                  )}
                {Array.isArray(visionSummary.colors) &&
                  visionSummary.colors.length > 0 && (
                    <p className="text-purple-700">
                      <b>{t.form.visionColors}:</b>{" "}
                      {(visionSummary.colors as string[]).join(", ")}
                    </p>
                  )}
                {(visionSummary.composition as string) && (
                  <p className="text-purple-700">
                    <b>{t.form.visionComposition}:</b>{" "}
                    {String(visionSummary.composition).slice(0, 120)}
                  </p>
                )}
                {Array.isArray(visionSummary.potential_issues) &&
                  visionSummary.potential_issues.length > 0 && (
                    <p className="mt-1 text-purple-600">
                      <b>{t.form.visionIssues}:</b>{" "}
                      {(visionSummary.potential_issues as string[]).slice(0, 3).join("; ")}
                    </p>
                  )}
              </div>
            )}
          </div>
        )}
        <textarea
          rows={2}
          value={imageDesc}
          onChange={(e) => setImageDesc(e.target.value)}
          placeholder={t.form.imagePlaceholder}
          className="mt-2 w-full rounded border border-gray-200 px-2 py-1 text-sm placeholder:text-gray-400 focus:border-blue-400 focus:outline-none"
        />
      </div>

      {/* Description */}
      <div>
        <label htmlFor="description" className="mb-1 block text-sm font-medium text-gray-600">
          {t.form.workDescription}
        </label>
        {prefillNotice && (
          <p className="mb-1 rounded border border-blue-200 bg-blue-50 px-2 py-1 text-xs text-blue-600">
            {t.form.prefillLoaded}
          </p>
        )}
        <textarea id="description" rows={4} value={description}
          onChange={(e) => setDescription(e.target.value)}
          onKeyDown={(e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
              e.preventDefault();
              if (!disabled) submit();
            }
          }}
          placeholder={t.form.descriptionPlaceholder}
          className="w-full rounded border border-gray-200 px-3 py-2 text-sm placeholder:text-gray-400 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
        />
        <p className="mt-1 text-xs text-gray-400">
          {description.length} {t.form.chars} ({t.form.minChars}) · {t.form.ctrlEnterHint}
        </p>

        {/* V2.3: completeness meter */}
        <div className="mt-2">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>{t.form.completeness} {completenessPct}%</span>
            {missingLabels.length > 0 && (
              <span className="text-amber-600">{t.form.missingLabel}：{missingLabels.join("、")}</span>
            )}
          </div>
          <div className="mt-1 h-1.5 w-full rounded-full bg-gray-100">
            <div className={`h-1.5 rounded-full transition-all ${completenessColor}`} style={{ width: `${Math.max(4, completenessPct)}%` }} />
          </div>
        </div>

        {/* V2.3: guided context fields */}
        <div className="mt-3 rounded border border-gray-200 bg-gray-50 p-3">
          <p className="text-xs font-medium text-gray-600">{t.form.guidedTitle}</p>
          <p className="mt-0.5 text-xs text-gray-400">{t.form.guidedHint}</p>
          {guesses.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {guesses.map((g, i) => (
                <button key={i} type="button" onClick={g.apply}
                  className="inline-flex items-center gap-1 rounded-full border border-purple-200 bg-purple-50 px-2 py-0.5 text-xs text-purple-700 hover:bg-purple-100">
                  <span className="rounded bg-purple-200 px-1 text-[10px]">{t.form.visionGuessTag}</span>
                  {g.value}
                  <span className="text-purple-400">· {t.form.applyGuess}</span>
                </button>
              ))}
            </div>
          )}
          <div className="mt-2 grid grid-cols-2 gap-2">
            <input value={gCategory} onChange={(e) => setGCategory(e.target.value)} placeholder={t.form.fieldCategory}
              className="rounded border border-gray-200 px-2 py-1 text-sm focus:border-blue-400 focus:outline-none" />
            <input value={gAudience} onChange={(e) => setGAudience(e.target.value)} placeholder={t.form.fieldAudience}
              className="rounded border border-gray-200 px-2 py-1 text-sm focus:border-blue-400 focus:outline-none" />
            <input value={gPriceBand} onChange={(e) => setGPriceBand(e.target.value)} placeholder={t.form.fieldPriceBand}
              className="rounded border border-gray-200 px-2 py-1 text-sm focus:border-blue-400 focus:outline-none" />
            <input value={gUseCase} onChange={(e) => setGUseCase(e.target.value)} placeholder={t.form.fieldUseCase}
              className="rounded border border-gray-200 px-2 py-1 text-sm focus:border-blue-400 focus:outline-none" />
          </div>
        </div>
      </div>

      <button type="button" onClick={() => setShowJudgment(!showJudgment)}
        className="text-sm text-blue-600 hover:text-blue-800 underline">
        {showJudgment ? t.form.toggleJudgmentHide : t.form.toggleJudgment}
      </button>

      {showJudgment && (
        <div className="space-y-3 rounded border bg-gray-50 p-4">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            {t.form.judgmentTitle}
          </p>
          <div>
            <label className="mb-1 block text-xs text-gray-600">{t.form.score}</label>
            <input type="number" min={0} max={100} value={judgeScore}
              onChange={(e) => setJudgeScore(e.target.value)} placeholder="70"
              className="w-24 rounded border border-gray-200 px-2 py-1 text-sm focus:border-blue-400 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-gray-600">{t.form.strengths}</label>
            <textarea rows={2} value={judgeStrengths}
              onChange={(e) => setJudgeStrengths(e.target.value)}
              className="w-full rounded border border-gray-200 px-2 py-1 text-sm placeholder:text-gray-400 focus:border-blue-400 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-gray-600">{t.form.weaknesses}</label>
            <textarea rows={2} value={judgeWeaknesses}
              onChange={(e) => setJudgeWeaknesses(e.target.value)}
              className="w-full rounded border border-gray-200 px-2 py-1 text-sm placeholder:text-gray-400 focus:border-blue-400 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-gray-600">{t.form.priorityFixes}</label>
            <textarea rows={2} value={judgeFixes}
              onChange={(e) => setJudgeFixes(e.target.value)}
              className="w-full rounded border border-gray-200 px-2 py-1 text-sm placeholder:text-gray-400 focus:border-blue-400 focus:outline-none"
            />
          </div>
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="mb-1 block text-xs text-gray-600">{t.form.targetAudience}</label>
              <input type="text" value={judgeAudience}
                onChange={(e) => setJudgeAudience(e.target.value)}
                className="w-full rounded border border-gray-200 px-2 py-1 text-sm focus:border-blue-400 focus:outline-none"
              />
            </div>
            <div className="flex-1">
              <label className="mb-1 block text-xs text-gray-600">{t.form.priceBand}</label>
              <input type="text" value={judgePriceBand}
                onChange={(e) => setJudgePriceBand(e.target.value)}
                className="w-full rounded border border-gray-200 px-2 py-1 text-sm focus:border-blue-400 focus:outline-none"
              />
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center gap-3">
        <button type="submit" disabled={disabled}
          className={`rounded px-6 py-2 text-sm font-medium text-white transition ${
            disabled
              ? "cursor-not-allowed bg-gray-300"
              : "bg-blue-600 hover:bg-blue-700 active:bg-blue-800"
          }`}>
          {loading ? t.form.running : `${t.form.run} ${t.tasks[taskType].label}`}
        </button>
        {tooShort && !loading && (
          <span className="text-xs text-amber-600">{t.form.tooShortHint}</span>
        )}
      </div>
    </form>
  );
}
