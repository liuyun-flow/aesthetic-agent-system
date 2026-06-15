"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useT } from "@/i18n";

const STEPS = [
  "welcome",
  "configure",
  "test",
  "first_training",
  "done",
] as const;

type StepKey = (typeof STEPS)[number];

export default function SetupPage() {
  const { t, lang } = useT();
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

  const [step, setStep] = useState<StepKey>("welcome");
  const [skipMode, setSkipMode] = useState(false);
  const [done, setDone] = useState(false);

  // Connection test states
  const [testingDeepSeek, setTestingDeepSeek] = useState(false);
  const [deepSeekResult, setDeepSeekResult] = useState<"ok" | "fail" | null>(null);
  const [testingVision, setTestingVision] = useState(false);
  const [visionResult, setVisionResult] = useState<"ok" | "fail" | null>(null);

  // Load system status for pre-filling
  const [systemStatus, setSystemStatus] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    fetch(`${base}/system/status`)
      .then((r) => r.json())
      .then((d) => setSystemStatus(d))
      .catch(() => {});
    // Also check if setup already completed
    fetch(`${base}/setup/status`)
      .then((r) => r.json())
      .then((d) => {
        if (d.setup_completed) setDone(true);
      })
      .catch(() => {});
  }, [base]);

  const markComplete = useCallback(async () => {
    try {
      await fetch(`${base}/setup/complete`, { method: "POST" });
      setDone(true);
    } catch {
      // still mark as done on the client side so the user isn't stuck
      setDone(true);
    }
  }, [base]);

  const testDeepSeek = async () => {
    setTestingDeepSeek(true);
    setDeepSeekResult(null);
    try {
      const res = await fetch(`${base}/settings/test-deepseek`, { method: "POST" });
      setDeepSeekResult(res.ok ? "ok" : "fail");
    } catch {
      setDeepSeekResult("fail");
    } finally {
      setTestingDeepSeek(false);
    }
  };

  const testVision = async () => {
    setTestingVision(true);
    setVisionResult(null);
    try {
      const res = await fetch(`${base}/settings/test-vision`, { method: "POST" });
      setVisionResult(res.ok ? "ok" : "fail");
    } catch {
      setVisionResult("fail");
    } finally {
      setTestingVision(false);
    }
  };

  const currentIndex = STEPS.indexOf(step);
  const progressPct = Math.round(((currentIndex + 1) / STEPS.length) * 100);

  const next = (s?: StepKey) => {
    if (s) { setStep(s); return; }
    const idx = STEPS.indexOf(step);
    if (idx < STEPS.length - 1) setStep(STEPS[idx + 1]);
  };
  const prev = () => {
    const idx = STEPS.indexOf(step);
    if (idx > 0) setStep(STEPS[idx - 1]);
  };

  const handleSkip = () => {
    setSkipMode(true);
    markComplete();
  };

  if (done) {
    return (
      <div className="mx-auto max-w-lg text-center py-12">
        <div className="text-4xl mb-4">🎉</div>
        <h2 className="text-xl font-semibold mb-2">{lang === "en" ? "Setup Complete!" : "设置完成！"}</h2>
        <p className="text-muted mb-6">
          {lang === "en"
            ? "You're ready to start your aesthetic training journey."
            : "你已经准备好开始审美训练了。"}
        </p>
        <div className="flex gap-3 justify-center">
          <Link
            href="/"
            className="rounded bg-accent px-6 py-2 text-sm font-medium text-white hover:bg-accent-deep transition"
          >
            {lang === "en" ? "Go to Workbench" : "进入训练工作台"}
          </Link>
          <Link
            href="/help"
            className="rounded border border-line px-6 py-2 text-sm font-medium text-ink-soft hover:bg-surface-2 transition"
          >
            {lang === "en" ? "View Help" : "查看帮助"}
          </Link>
        </div>
        <button
          onClick={() => {
            setDone(false);
            setStep("welcome");
          }}
          className="mt-4 text-xs text-muted hover:text-ink-soft underline"
        >
          {lang === "en" ? "Re-open wizard" : "重新打开向导"}
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl">
      {/* Progress bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-muted">
            {lang === "en" ? "Step" : "步骤"} {currentIndex + 1} / {STEPS.length}
          </span>
          {!skipMode && (
            <button onClick={handleSkip} className="text-xs text-muted hover:text-ink-soft underline">
              {lang === "en" ? "Skip wizard" : "跳过向导"}
            </button>
          )}
        </div>
        <div className="h-1.5 rounded-full bg-surface-2">
          <div
            className="h-1.5 rounded-full bg-accent transition-all duration-300"
            style={{ width: `${progressPct}%` }}
          />
        </div>
        {/* Step indicators */}
        <div className="flex justify-between mt-2">
          {STEPS.map((s, i) => (
            <button
              key={s}
              onClick={() => setStep(s)}
              className={`text-xs transition ${
                i === currentIndex
                  ? "font-semibold text-accent"
                  : i < currentIndex
                  ? "text-accent"
                  : "text-gray-300"
              }`}
            >
              {STEP_LABELS[s]?.[lang === "en" ? "en" : "zh"] || s}
            </button>
          ))}
        </div>
      </div>

      {/* Step content */}
      <div className="rounded-xl border bg-surface p-6 shadow-soft min-h-[320px]">
        {step === "welcome" && <WelcomeStep t={t} lang={lang} />}
        {step === "configure" && (
          <ConfigureStep
            t={t}
            lang={lang}
            systemStatus={systemStatus}
          />
        )}
        {step === "test" && (
          <TestStep
            t={t}
            lang={lang}
            testingDeepSeek={testingDeepSeek}
            deepSeekResult={deepSeekResult}
            testDeepSeek={testDeepSeek}
            testingVision={testingVision}
            visionResult={visionResult}
            testVision={testVision}
            systemStatus={systemStatus}
          />
        )}
        {step === "first_training" && <FirstTrainingStep t={t} lang={lang} />}
        {step === "done" && (
          <DoneStep
            t={t}
            lang={lang}
            onComplete={markComplete}
          />
        )}
      </div>

      {/* Navigation buttons */}
      <div className="flex justify-between mt-4">
        <button
          onClick={prev}
          disabled={currentIndex === 0}
          className={`rounded px-4 py-2 text-sm font-medium transition ${
            currentIndex === 0
              ? "cursor-not-allowed text-gray-300"
              : "text-ink-soft hover:bg-surface-2"
          }`}
        >
          ← {lang === "en" ? "Back" : "上一步"}
        </button>
        {step !== "done" && (
          <button
            onClick={() => next()}
            className="rounded bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-deep transition"
          >
            {lang === "en" ? "Next" : "下一步"} →
          </button>
        )}
      </div>
    </div>
  );
}

/* ── Step Label Map ─────────────────────────────────────────────────── */

const STEP_LABELS: Record<StepKey, { zh: string; en: string }> = {
  welcome: { zh: "欢迎", en: "Welcome" },
  configure: { zh: "配置", en: "Configure" },
  test: { zh: "测试", en: "Test" },
  first_training: { zh: "训练", en: "Training" },
  done: { zh: "完成", en: "Done" },
};

/* ── Step Components ────────────────────────────────────────────────── */

function WelcomeStep({ t, lang }: { t: ReturnType<typeof useT>["t"]; lang: string }) {
  const zh = lang !== "en";
  return (
    <div>
      <h2 className="text-lg font-semibold mb-3">
        {zh ? "欢迎使用审美训练智能体" : "Welcome to Aesthetic Training Agent"}
      </h2>
      <div className="text-sm text-ink-soft space-y-3">
        <p>
          {zh
            ? "这不是普通的图片分析工具。这是一个帮你训练审美判断力的智能体。"
            : "This is not a regular image analysis tool. It's an agent that helps you train your aesthetic judgment."}
        </p>
        <div className="rounded bg-amber-50 border border-amber-200 p-3 text-amber-800">
          <p className="font-medium mb-1">
            {zh ? "🎯 核心理念" : "🎯 Core Idea"}
          </p>
          <p>
            {zh
              ? "AI 不是裁判，是镜子。它帮你看到自己没注意到的细节，让你慢慢建立自己的审美框架。你才是最终的判断者。"
              : "AI is not the judge, it's a mirror. It helps you see details you might miss, so you can gradually build your own aesthetic framework. You are the final judge."}
          </p>
        </div>
        <p>
          {zh
            ? "使用流程：上传图片 → AI 自动描述 → 你先自评 → AI 分析/评分/批评 → 对比你和 AI 的判断差异 → 学习成长"
            : "Workflow: Upload image → AI auto-describes → You self-assess → AI analyzes/scores/critiques → Compare your judgment vs AI → Learn and grow"}
        </p>
        <p>
          {zh
            ? "开始之前，需要先配置两个模型："
            : "Before starting, you need to configure two models:"}
        </p>
        <ul className="list-disc list-inside space-y-1">
          <li>
            <b>DeepSeek</b> — {zh ? "审美推理引擎（分析/评分/迭代/对比）" : "Aesthetic reasoning engine (analysis/critique/iteration/comparison)"}
          </li>
          <li>
            <b>OpenAI Vision</b> — {zh ? "图片文字描述（把你上传的图片转成文字描述）" : "Image-to-text description (converts your uploaded images into text descriptions)"}
          </li>
        </ul>
      </div>
    </div>
  );
}

function ConfigureStep({
  t,
  lang,
  systemStatus,
}: {
  t: ReturnType<typeof useT>["t"];
  lang: string;
  systemStatus: Record<string, unknown> | null;
}) {
  const zh = lang !== "en";
  const dsOk = (systemStatus?.deepseek as Record<string, unknown>)?.configured;
  const visOk = (systemStatus?.vision as Record<string, unknown>)?.configured;
  const visPlaceholder = (systemStatus?.vision as Record<string, unknown>)?.is_placeholder;

  return (
    <div>
      <h2 className="text-lg font-semibold mb-3">
        {zh ? "配置模型 API Key" : "Configure Model API Keys"}
      </h2>
      <div className="text-sm text-ink-soft space-y-3">
        <p>
          {zh
            ? "两个模型都需要 API Key 才能工作。所有 Key 保存在你的本地机器上，不会上传到任何地方。"
            : "Both models need API keys to work. All keys are stored locally on your machine and never uploaded anywhere."}
        </p>

        {/* DeepSeek */}
        <div className="rounded border p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium text-ink">DeepSeek</span>
            {dsOk !== undefined && (
              <span className={`rounded px-2 py-0.5 text-xs font-medium ${dsOk ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                {dsOk ? (zh ? "已配置" : "Configured") : (zh ? "未配置" : "Not configured")}
              </span>
            )}
          </div>
          <p className="text-xs text-muted mb-2">
            {zh
              ? "注册 DeepSeek 获取 API Key：platform.deepseek.com → API Keys → 创建 → 复制 sk- 开头的 Key"
              : "Get a DeepSeek API Key: platform.deepseek.com → API Keys → Create → Copy the key starting with sk-"}
          </p>
          <Link
            href="/settings"
            className="inline-block text-xs text-accent hover:underline"
          >
            {zh ? "去设置页配置 →" : "Go to Settings →"}
          </Link>
        </div>

        {/* Vision */}
        <div className="rounded border p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium text-ink">OpenAI Vision</span>
            {visOk !== undefined && (
              <span
                className={`rounded px-2 py-0.5 text-xs font-medium ${
                  visOk
                    ? "bg-green-100 text-green-700"
                    : visPlaceholder
                    ? "bg-amber-100 text-amber-700"
                    : "bg-red-100 text-red-700"
                }`}
              >
                {visOk
                  ? zh ? "已配置" : "Configured"
                  : visPlaceholder
                  ? zh ? "占位模式" : "Placeholder"
                  : zh ? "未配置" : "Not configured"}
              </span>
            )}
          </div>
          <p className="text-xs text-muted mb-2">
            {zh
              ? "注册 OpenAI 获取 API Key：platform.openai.com → API Keys → 创建 → 复制 sk- 开头的 Key。注意：你需要一个有额度的 OpenAI 账号。"
              : "Get an OpenAI API Key: platform.openai.com → API Keys → Create → Copy the key starting with sk-. Note: you need an OpenAI account with credits."}
          </p>
          <p className="text-xs text-muted mb-2">
            {zh
              ? "如果暂时没有 OpenAI Key，可以使用「占位模式」先用固定示例体验流程。图片描述不会匹配你的实际图片。"
              : "If you don't have an OpenAI key yet, you can use 'Placeholder' mode to try the workflow with sample descriptions. Descriptions won't match your actual images."}
          </p>
          <Link
            href="/settings"
            className="inline-block text-xs text-accent hover:underline"
          >
            {zh ? "去设置页配置 →" : "Go to Settings →"}
          </Link>
        </div>

        <div className="rounded bg-accent-wash border border-accent-soft p-3 text-xs text-accent">
          💡{" "}
          {zh
            ? "配置完后点击下一步，我们来测试连接。"
            : "After configuring, click Next to test the connections."}
        </div>
      </div>
    </div>
  );
}

function TestStep({
  t,
  lang,
  testingDeepSeek,
  deepSeekResult,
  testDeepSeek,
  testingVision,
  visionResult,
  testVision,
  systemStatus,
}: {
  t: ReturnType<typeof useT>["t"];
  lang: string;
  testingDeepSeek: boolean;
  deepSeekResult: "ok" | "fail" | null;
  testDeepSeek: () => void;
  testingVision: boolean;
  visionResult: "ok" | "fail" | null;
  testVision: () => void;
  systemStatus: Record<string, unknown> | null;
}) {
  const zh = lang !== "en";
  const dsConfigured = (systemStatus?.deepseek as Record<string, unknown>)?.configured;
  const visConfigured = (systemStatus?.vision as Record<string, unknown>)?.configured;

  return (
    <div>
      <h2 className="text-lg font-semibold mb-3">
        {zh ? "测试模型连接" : "Test Model Connections"}
      </h2>
      <div className="text-sm text-ink-soft space-y-4">
        <p>
          {zh
            ? "测试一下两个模型是否能正常连接。如果失败，请检查 API Key 是否正确、网络是否通畅。"
            : "Test whether both models can connect. If it fails, check your API keys and network."}
        </p>

        {/* DeepSeek test */}
        <div className="rounded border p-3">
          <div className="flex items-center justify-between">
            <div>
              <span className="font-medium text-ink text-sm">DeepSeek</span>
              {dsConfigured === false && (
                <span className="ml-2 text-xs text-muted">
                  ({zh ? "未配置 Key" : "No key configured"})
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              {deepSeekResult === "ok" && (
                <span className="text-xs text-green-600 font-medium">✓ {zh ? "连接成功" : "Connected"}</span>
              )}
              {deepSeekResult === "fail" && (
                <span className="text-xs text-red-600 font-medium">✗ {zh ? "连接失败" : "Failed"}</span>
              )}
              <button
                onClick={testDeepSeek}
                disabled={testingDeepSeek || dsConfigured === false}
                className={`rounded px-3 py-1 text-xs font-medium transition ${
                  testingDeepSeek || dsConfigured === false
                    ? "cursor-not-allowed bg-gray-200 text-muted"
                    : "bg-accent-wash text-accent hover:bg-accent-soft"
                }`}
              >
                {testingDeepSeek ? (zh ? "测试中…" : "Testing…") : (zh ? "测试连接" : "Test")}
              </button>
            </div>
          </div>
        </div>

        {/* Vision test */}
        <div className="rounded border p-3">
          <div className="flex items-center justify-between">
            <div>
              <span className="font-medium text-ink text-sm">OpenAI Vision</span>
              {visConfigured === false && (
                <span className="ml-2 text-xs text-muted">
                  ({zh ? "未配置 Key" : "No key configured"})
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              {visionResult === "ok" && (
                <span className="text-xs text-green-600 font-medium">✓ {zh ? "连接成功" : "Connected"}</span>
              )}
              {visionResult === "fail" && (
                <span className="text-xs text-red-600 font-medium">✗ {zh ? "连接失败" : "Failed"}</span>
              )}
              <button
                onClick={testVision}
                disabled={testingVision || visConfigured === false}
                className={`rounded px-3 py-1 text-xs font-medium transition ${
                  testingVision || visConfigured === false
                    ? "cursor-not-allowed bg-gray-200 text-muted"
                    : "bg-accent-wash text-accent hover:bg-accent-soft"
                }`}
              >
                {testingVision ? (zh ? "测试中…" : "Testing…") : (zh ? "测试连接" : "Test")}
              </button>
            </div>
          </div>
        </div>

        <div className="rounded bg-accent-wash border border-accent-soft p-3 text-xs text-accent">
          💡{" "}
          {zh
            ? "即使测试失败也可以继续，之后随时可以在设置页重新配置。"
            : "You can continue even if tests fail — you can always reconfigure later in Settings."}
        </div>
      </div>
    </div>
  );
}

function FirstTrainingStep({ t, lang }: { t: ReturnType<typeof useT>["t"]; lang: string }) {
  const zh = lang !== "en";
  return (
    <div>
      <h2 className="text-lg font-semibold mb-3">
        {zh ? "如何完成第一次审美训练" : "How to Complete Your First Training"}
      </h2>
      <div className="text-sm text-ink-soft space-y-3">
        <p>
          {zh
            ? "一次完整的审美训练包含以下步骤："
            : "A complete aesthetic training session consists of:"}
        </p>

        <ol className="list-decimal list-inside space-y-2 ml-2">
          <li>
            <b>{zh ? "上传图片" : "Upload an image"}</b>
            <br />
            <span className="text-xs text-muted">
              {zh
                ? "支持 jpg/png/webp，最大 10MB。上传后点击「自动生成图片描述」，AI 会把图片内容转成文字。"
                : "Supports jpg/png/webp, max 10MB. After upload, click 'Auto-generate description' to convert the image to text."}
            </span>
          </li>
          <li>
            <b>{zh ? "填写作品描述" : "Write a work description"}</b>
            <br />
            <span className="text-xs text-muted">
              {zh
                ? "用文字补充描述你的作品：颜色、布局、字体、材质、氛围、目标用户等。至少 10 个字符。"
                : "Describe your work in words: colors, layout, fonts, materials, mood, target audience, etc. At least 10 characters."}
            </span>
          </li>
          <li>
            <b>{zh ? "先自评（重要！）" : "Self-assess first (important!)"}</b>
            <br />
            <span className="text-xs text-muted">
              {zh
                ? "点击「+ 填写我的初步判断」，给出你的评分、优缺点、目标用户、价格带。这是训练的核心——你不先判断，就无法知道自己和 AI 的差距在哪里。"
                : "Click '+ Add my own judgment' and give your score, strengths, weaknesses, target audience, and price band. This is the core of training — if you don't judge first, you can't see where you and AI differ."}
            </span>
          </li>
          <li>
            <b>{zh ? "选择任务类型并运行" : "Choose task type and run"}</b>
            <br />
            <span className="text-xs text-muted">
              {zh
                ? "分析：9 个美学维度分解 | 评分：结构化打分+问题+修复 | 迭代：3-5 个改版方向。"
                : "Analyze: 9 aesthetic dimensions | Critique: structured scoring + issues + fixes | Iterate: 3-5 design alternatives."}
            </span>
          </li>
          <li>
            <b>{zh ? "查看判断差异" : "Review the judgment gap"}</b>
            <br />
            <span className="text-xs text-muted">
              {zh
                ? "对比你和 AI 在评分、问题识别、修复建议上的差异。这是学习的核心——你哪对了？哪漏了？哪误判了？"
                : "Compare your judgment vs AI on scoring, issues, and fixes. This is where learning happens — what did you get right? What did you miss? What did you misjudge?"}
            </span>
          </li>
        </ol>

        <div className="rounded bg-amber-50 border border-amber-200 p-3 text-xs text-amber-800">
          ⚠️{" "}
          {zh
            ? "一定要先自评再看 AI 结果。如果你先看 AI 的分析，自评就失去意义了——你会被 AI 的观点影响。"
            : "Always self-assess before seeing AI results. If you see AI's analysis first, your self-assessment becomes biased and the training loses its value."}
        </div>
      </div>
    </div>
  );
}

function DoneStep({
  t,
  lang,
  onComplete,
}: {
  t: ReturnType<typeof useT>["t"];
  lang: string;
  onComplete: () => void;
}) {
  const zh = lang !== "en";
  return (
    <div>
      <h2 className="text-lg font-semibold mb-3">
        {zh ? "准备就绪！" : "You're Ready!"}
      </h2>
      <div className="text-sm text-ink-soft space-y-3">
        <p>
          {zh
            ? "你已经了解了这个工具的基本流程。现在可以开始你的第一次审美训练了。"
            : "You now understand the basic workflow. Time to start your first aesthetic training."}
        </p>
        <div className="rounded bg-green-50 border border-green-200 p-3 text-xs text-green-800 space-y-1">
          <p className="font-medium">
            {zh ? "✅ 配置检查清单" : "✅ Configuration Checklist"}
          </p>
          <ul className="list-disc list-inside">
            <li>DeepSeek API Key — {zh ? "审美推理引擎" : "Aesthetic reasoning engine"}</li>
            <li>OpenAI Vision — {zh ? "图片自动描述" : "Auto image description"}</li>
            <li>{zh ? "了解训练流程" : "Understand the training flow"}</li>
            <li>{zh ? "知道要先自评再看 AI" : "Know to self-assess before AI"}</li>
          </ul>
        </div>
        <p>
          {zh
            ? "随时可以查看帮助页面获取更多指导，或重新运行本向导。"
            : "You can always visit the Help page for more guidance, or re-run this wizard."}
        </p>
        <button
          onClick={onComplete}
          className="w-full rounded bg-accent px-4 py-3 text-sm font-medium text-white hover:bg-accent-deep transition mt-2"
        >
          {zh ? "完成向导，进入训练工作台" : "Complete Wizard, Enter Workbench"}
        </button>
      </div>
    </div>
  );
}
