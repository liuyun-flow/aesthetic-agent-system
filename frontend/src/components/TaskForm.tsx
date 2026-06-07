"use client";

import { useState, useRef, useEffect, type FormEvent } from "react";
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
}

const TASK_KEYS = ["analyze", "critique", "iterate"] as const;

export default function TaskForm({ onSubmit, loading }: Props) {
  const { t } = useT();
  const [description, setDescription] = useState("");
  const [taskType, setTaskType] = useState<TaskType>("analyze");
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

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
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
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : t.common.uploadFailed);
    } finally {
      setUploading(false);
    }
  };

  const handleAutoDescribe = async () => {
    if (imageId === null) return;
    setDescribing(true);
    setDescribeError(null);
    setVisionSummary(null);
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${base}/images/${imageId}/describe`, { method: "POST" });
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
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
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

    onSubmit(description.trim(), taskType, judgment, image);
  };

  const disabled = loading || description.trim().length < 10;

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
      <div className="rounded border bg-gray-50 p-3">
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
        <textarea id="description" rows={4} value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder={t.form.descriptionPlaceholder}
          className="w-full rounded border border-gray-200 px-3 py-2 text-sm placeholder:text-gray-400 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
        />
        <p className="mt-1 text-xs text-gray-400">
          {description.length} {t.form.chars} ({t.form.minChars})
        </p>
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

      <button type="submit" disabled={disabled}
        className={`rounded px-6 py-2 text-sm font-medium text-white transition ${
          disabled
            ? "cursor-not-allowed bg-gray-300"
            : "bg-blue-600 hover:bg-blue-700 active:bg-blue-800"
        }`}>
        {loading ? t.form.running : `${t.form.run} ${t.tasks[taskType].label}`}
      </button>
    </form>
  );
}
