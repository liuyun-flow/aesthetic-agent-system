"use client";

import { useEffect, useState, useCallback } from "react";
import { useT } from "@/i18n";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

interface SettingsStatus {
  deepseek: {
    is_configured: boolean;
    api_key_masked: string;
    base_url: string;
    default_model: string;
    reasoning_model: string;
  };
  vision: {
    provider: string;
    is_configured: boolean;
    openai_api_key_masked: string;
    openai_vision_model: string;
  };
}

// ── V2.1: System Diagnostics Panel ──────────────────────────────────────

interface PreflightData {
  version: string;
  backend: string;
  database: { status: string; path: string; exists: boolean; writable: boolean; size_kb: number };
  config_dir: { status: string; path: string; exists: boolean; writable: boolean };
  uploads_dir: { status: string; path: string; exists: boolean; writable: boolean; file_count: number };
  deepseek: { configured: boolean; model: string; reasoning_model: string; hint: string };
  vision: { configured: boolean; provider: string; is_placeholder: boolean; hint: string };
  embedding: { configured: boolean; hint: string };
  recommendations: string[];
  all_ok: boolean;
  is_docker: boolean;
}

function statusIcon(ok: boolean): string { return ok ? "✅" : "❌"; }

/* ── V2.5: LLM usage telemetry ─────────────────────────────────────── */

interface UsageData {
  total_calls: number;
  total_tokens: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  avg_latency_ms: number | null;
  by_model: { model: string; calls: number; total_tokens: number }[];
}

function UsageStat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded border bg-gray-50 px-3 py-2">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-sm font-semibold text-gray-800">{value}</p>
    </div>
  );
}

function UsagePanel() {
  const [data, setData] = useState<UsageData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${BASE}/system/usage`)
      .then((r) => (r.ok ? r.json() : null))
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="rounded border bg-white p-5 shadow-sm">
      <h3 className="text-base font-semibold text-gray-700 mb-3">用量统计（LLM）</h3>
      {loading ? (
        <p className="text-xs text-gray-400">加载中…</p>
      ) : !data || data.total_calls === 0 ? (
        <p className="text-xs text-gray-400">
          暂无调用记录。运行分析 / 评分 / 迭代后，这里会显示累计 token 与平均延迟。
        </p>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
            <UsageStat label="总调用次数" value={data.total_calls} />
            <UsageStat label="总 token" value={data.total_tokens.toLocaleString()} />
            <UsageStat
              label="输入 / 输出 token"
              value={`${data.total_prompt_tokens.toLocaleString()} / ${data.total_completion_tokens.toLocaleString()}`}
            />
            <UsageStat
              label="平均延迟"
              value={data.avg_latency_ms != null ? `${data.avg_latency_ms} ms` : "--"}
            />
          </div>
          <div className="space-y-1">
            {data.by_model.map((m) => (
              <div key={m.model} className="flex items-center gap-2 text-xs">
                <span className="flex-1 truncate font-medium text-gray-700">{m.model || "?"}</span>
                <span className="text-gray-500">{m.calls} 次</span>
                <span className="w-28 text-right text-gray-500">
                  {m.total_tokens.toLocaleString()} token
                </span>
              </div>
            ))}
          </div>
          <p className="mt-2 text-xs text-gray-400">
            token 来自各次调用返回的 usage；成本请按你所用模型的计价自行估算。
          </p>
        </>
      )}
    </section>
  );
}

function DiagnosticsPanel() {
  const [data, setData] = useState<PreflightData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDiagnostics = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${BASE}/system/preflight`);
      if (!res.ok) throw new Error("无法获取诊断数据");
      setData(await res.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "诊断失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDiagnostics(); }, []);

  if (loading) {
    return (
      <section className="rounded border bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-base font-semibold text-gray-700">系统诊断</h3>
        </div>
        <p className="text-xs text-gray-400">正在检测系统状态…</p>
      </section>
    );
  }

  if (error || !data) {
    return (
      <section className="rounded border bg-red-50 border-red-200 p-5 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-base font-semibold text-gray-700">系统诊断</h3>
          <button onClick={fetchDiagnostics} className="text-xs text-blue-600 underline">重新检测</button>
        </div>
        <p className="text-xs text-red-500">{error || "诊断数据不可用"}</p>
      </section>
    );
  }

  const Row = ({ label, ok, detail }: { label: string; ok: boolean; detail: string }) => (
    <div className="flex items-center gap-2 text-xs py-1">
      <span className="w-5 text-center">{statusIcon(ok)}</span>
      <span className="w-24 shrink-0 font-medium text-gray-700">{label}</span>
      <span className={`flex-1 ${ok ? "text-green-600" : "text-red-500"}`}>{detail}</span>
    </div>
  );

  return (
    <section className="rounded border bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-base font-semibold text-gray-700">
          系统诊断
          <span className="ml-2 text-xs font-normal text-gray-400">{data.version}</span>
        </h3>
        <button onClick={fetchDiagnostics} className="text-xs text-blue-600 underline hover:text-blue-800">重新检测</button>
      </div>

      <div className="space-y-0.5 mb-3">
        <Row label="后端服务" ok={data.backend === "ok"} detail={data.backend === "ok" ? "正常" : "异常"} />
        <Row label="数据库" ok={data.database.status === "ok"} detail={data.database.status === "ok" ? `正常 (${data.database.size_kb} KB)` : "异常"} />
        <Row label="配置目录" ok={data.config_dir.writable} detail={data.config_dir.writable ? "可读写" : "不可写"} />
        <Row label="上传目录" ok={data.uploads_dir.writable} detail={data.uploads_dir.writable ? `可读写，${data.uploads_dir.file_count} 个文件` : "不可写"} />
        <Row label="DeepSeek" ok={data.deepseek.configured} detail={data.deepseek.configured ? `已配置 (${data.deepseek.model})` : "未配置"} />
        <Row
          label="Vision"
          ok={data.vision.configured || data.vision.is_placeholder}
          detail={data.vision.is_placeholder ? "占位模式" : data.vision.configured ? `已配置 (${data.vision.provider})` : "未配置"}
        />
        <Row label="Embedding" ok={data.embedding.configured} detail={data.embedding.configured ? "已配置" : "未配置"} />
      </div>

      {(data.recommendations ?? []).length > 0 && (
        <div className="rounded border border-blue-200 bg-blue-50 p-3">
          <p className="text-xs font-medium text-blue-700 mb-1">建议操作</p>
          <ul className="space-y-0.5">
            {(data.recommendations ?? []).map((r, i) => (
              <li key={i} className="text-xs text-blue-600">• {r}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

export default function SettingsPage() {
  const { t } = useT();

  // ── Status from server ─────────────────────────────────────────────
  const [status, setStatus] = useState<SettingsStatus | null>(null);
  const [loading, setLoading] = useState(true);

  // ── Form state ─────────────────────────────────────────────────────
  const [dsKey, setDsKey] = useState("");
  const [dsBaseUrl, setDsBaseUrl] = useState("https://api.deepseek.com");
  const [dsDefaultModel, setDsDefaultModel] = useState("deepseek-v4-flash");
  const [dsReasoningModel, setDsReasoningModel] = useState("deepseek-v4-pro");
  const [visionProvider, setVisionProvider] = useState("placeholder");
  const [openaiKey, setOpenaiKey] = useState("");
  const [openaiModel, setOpenaiModel] = useState("gpt-4o-mini");

  // ── Action states ──────────────────────────────────────────────────
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [testingDs, setTestingDs] = useState(false);
  const [dsTestResult, setDsTestResult] = useState<{ ok: boolean; text: string } | null>(null);
  const [testingVision, setTestingVision] = useState(false);
  const [visionTestResult, setVisionTestResult] = useState<{ ok: boolean; text: string } | null>(null);

  // ── Load status on mount ───────────────────────────────────────────
  const [fetchError, setFetchError] = useState(false);
  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${BASE}/settings`);
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
        setFetchError(false);
        setDsBaseUrl(data.deepseek.base_url);
        setDsDefaultModel(data.deepseek.default_model);
        setDsReasoningModel(data.deepseek.reasoning_model);
        setVisionProvider(data.vision.provider);
        setOpenaiModel(data.vision.openai_vision_model);
      } else {
        setFetchError(true);
      }
    } catch {
      setFetchError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);

  // ── Save ───────────────────────────────────────────────────────────
  const handleSave = async () => {
    setSaving(true);
    setSaveMsg(null);
    try {
      const body: Record<string, string> = {};
      if (dsKey) body.deepseek_api_key = dsKey;
      if (dsBaseUrl) body.deepseek_base_url = dsBaseUrl;
      if (dsDefaultModel) body.deepseek_default_model = dsDefaultModel;
      if (dsReasoningModel) body.deepseek_reasoning_model = dsReasoningModel;
      if (visionProvider) body.vision_provider = visionProvider;
      if (openaiKey) body.openai_api_key = openaiKey;
      if (openaiModel) body.openai_vision_model = openaiModel;

      const res = await fetch(`${BASE}/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        setSaveMsg({ ok: true, text: t.settings.saved });
        setDsKey(""); // clear key field after save
        setOpenaiKey("");
        await fetchStatus(); // refresh masked status
      } else {
        const err = await res.json().catch(() => ({}));
        setSaveMsg({ ok: false, text: err.detail || t.settings.saveError });
      }
    } catch {
      setSaveMsg({ ok: false, text: t.settings.saveError });
    } finally {
      setSaving(false);
    }
  };

  // ── Test DeepSeek ──────────────────────────────────────────────────
  const handleTestDs = async () => {
    setTestingDs(true);
    setDsTestResult(null);
    try {
      // If user typed a new key but hasn't saved, save first
      if (dsKey) await handleSaveSilent();
      const res = await fetch(`${BASE}/settings/test-deepseek`, { method: "POST" });
      const data = await res.json();
      setDsTestResult({
        ok: data.success,
        text: data.message,
      });
    } catch {
      setDsTestResult({ ok: false, text: t.settings.testFailed });
    } finally {
      setTestingDs(false);
    }
  };

  // ── Test Vision ────────────────────────────────────────────────────
  const handleTestVision = async () => {
    setTestingVision(true);
    setVisionTestResult(null);
    try {
      if (openaiKey) await handleSaveSilent();
      const res = await fetch(`${BASE}/settings/test-vision`, { method: "POST" });
      const data = await res.json();
      setVisionTestResult({
        ok: data.success,
        text: data.message,
      });
    } catch {
      setVisionTestResult({ ok: false, text: t.settings.testFailed });
    } finally {
      setTestingVision(false);
    }
  };

  // ── Silent save (for test-before-save flow) ───────────────────────
  const handleSaveSilent = async () => {
    const body: Record<string, string> = {};
    if (dsKey) body.deepseek_api_key = dsKey;
    if (openaiKey) body.openai_api_key = openaiKey;
    if (visionProvider) body.vision_provider = visionProvider;
    await fetch(`${BASE}/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).catch(() => {});
    // Don't clear keys — user may test multiple times
  };

  // ── Clear key ──────────────────────────────────────────────────────
  const handleClearKey = async (keyType: "deepseek" | "openai") => {
    try {
      const res = await fetch(`${BASE}/settings/clear-key`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key_type: keyType }),
      });
      if (res.ok) {
        setDsKey("");
        setOpenaiKey("");
        setSaveMsg({ ok: true, text: t.settings.keyCleared });
        await fetchStatus();
      } else {
        const err = await res.json().catch(() => ({}));
        setSaveMsg({ ok: false, text: err.detail || t.settings.saveError });
      }
    } catch {
      setSaveMsg({ ok: false, text: t.settings.saveError });
    }
  };

  // ── Helpers ────────────────────────────────────────────────────────
  const statusBadge = (ok: boolean) =>
    ok
      ? { cls: "bg-green-100 text-green-700", label: t.settings.configured }
      : { cls: "bg-red-100 text-red-700", label: t.settings.notConfigured };

  const dsBadge = statusBadge(status?.deepseek.is_configured ?? false);
  const vsBadge = statusBadge(status?.vision.is_configured ?? false);
  const hasOpenaiKey = Boolean(status?.vision.openai_api_key_masked);

  if (loading) {
    return <div className="text-center text-sm text-gray-400 py-12">{t.common.loading}</div>;
  }

  if (fetchError && !status) {
    return (
      <div className="text-center py-12">
        <p className="text-sm text-red-500 mb-2">{t.settings.loadError || "无法加载设置，请确认后端服务已启动。"}</p>
        <button
          onClick={() => { setLoading(true); setFetchError(false); fetchStatus(); }}
          className="rounded bg-blue-600 px-4 py-2 text-xs font-medium text-white hover:bg-blue-700"
        >
          {t.settings.retry || "重试"}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-800">{t.settings.title}</h2>

      {/* ── V2.1: System Diagnostics ───────────────────────────────── */}
      <DiagnosticsPanel />

      {/* ── V2.5: LLM usage telemetry ──────────────────────────────── */}
      <UsagePanel />

      {/* ── DeepSeek Section ────────────────────────────────────────── */}
      <section className="rounded border bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold text-gray-700">{t.settings.deepseekTitle}</h3>
          <span className={`rounded px-2 py-0.5 text-xs font-medium ${dsBadge.cls}`}>
            {dsBadge.label}
          </span>
        </div>

        <div className="space-y-3">
          {/* API Key */}
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600">
              {t.settings.apiKey}
              {status?.deepseek.api_key_masked && (
                <span className="ml-2 text-green-600 font-normal">
                  {status.deepseek.api_key_masked}
                </span>
              )}
            </label>
            <input
              type="password"
              value={dsKey}
              onChange={(e) => setDsKey(e.target.value)}
              placeholder={status?.deepseek.is_configured ? t.settings.keyMasked : t.settings.apiKeyPlaceholder}
              className={`w-full rounded border border-gray-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400 ${
                status?.deepseek.is_configured && !dsKey ? "bg-green-50 placeholder:text-green-500" : "placeholder:text-gray-400"
              }`}
            />
            <p className="mt-1 text-xs text-gray-400">{t.settings.apiKeyHint}</p>
          </div>

          {/* Base URL */}
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600">{t.settings.baseUrl}</label>
            <input
              type="text"
              value={dsBaseUrl}
              onChange={(e) => setDsBaseUrl(e.target.value)}
              className="w-full rounded border border-gray-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
            />
          </div>

          {/* Models row */}
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="mb-1 block text-xs font-medium text-gray-600">{t.settings.defaultModel}</label>
              <select
                value={dsDefaultModel}
                onChange={(e) => setDsDefaultModel(e.target.value)}
                className="w-full rounded border border-gray-200 px-2 py-2 text-sm focus:border-blue-400 focus:outline-none"
              >
                <option value="deepseek-v4-flash">deepseek-v4-flash</option>
                <option value="deepseek-v4-pro">deepseek-v4-pro</option>
                <option value="deepseek-chat">deepseek-chat</option>
                <option value="deepseek-reasoner">deepseek-reasoner</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="mb-1 block text-xs font-medium text-gray-600">{t.settings.reasoningModel}</label>
              <select
                value={dsReasoningModel}
                onChange={(e) => setDsReasoningModel(e.target.value)}
                className="w-full rounded border border-gray-200 px-2 py-2 text-sm focus:border-blue-400 focus:outline-none"
              >
                <option value="deepseek-v4-pro">deepseek-v4-pro</option>
                <option value="deepseek-v4-flash">deepseek-v4-flash</option>
                <option value="deepseek-chat">deepseek-chat</option>
                <option value="deepseek-reasoner">deepseek-reasoner</option>
              </select>
            </div>
          </div>

          {/* DeepSeek actions */}
          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={handleTestDs}
              disabled={testingDs}
              className={`rounded px-4 py-2 text-xs font-medium text-white transition ${
                testingDs ? "cursor-not-allowed bg-gray-300" : "bg-teal-600 hover:bg-teal-700"
              }`}
            >
              {testingDs ? t.settings.testing : t.settings.testConnection}
            </button>
            <button
              type="button"
              onClick={() => handleClearKey("deepseek")}
              className="rounded border border-red-200 px-4 py-2 text-xs font-medium text-red-600 hover:bg-red-50 transition"
            >
              {t.settings.clearKey}
            </button>
          </div>
          {dsTestResult && (
            <div
              className={`rounded border px-3 py-2 text-xs ${
                dsTestResult.ok
                  ? "border-green-200 bg-green-50 text-green-700"
                  : "border-red-200 bg-red-50 text-red-700"
              }`}
            >
              {dsTestResult.text}
            </div>
          )}
        </div>
      </section>

      {/* ── Vision Section ───────────────────────────────────────────── */}
      <section className="rounded border bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold text-gray-700">{t.settings.visionTitle}</h3>
          <span className={`rounded px-2 py-0.5 text-xs font-medium ${vsBadge.cls}`}>
            {vsBadge.label}
          </span>
        </div>

        <div className="space-y-3">
          {/* Provider */}
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600">{t.settings.provider}</label>
            <select
              value={visionProvider}
              onChange={(e) => setVisionProvider(e.target.value)}
              className="w-full rounded border border-gray-200 px-2 py-2 text-sm focus:border-blue-400 focus:outline-none"
            >
              <option value="placeholder">{t.settings.providerPlaceholder}</option>
              <option value="openai">{t.settings.providerOpenAI}</option>
            </select>
          </div>

          {/* OpenAI Key (shown only when provider is openai) */}
          {visionProvider === "openai" && (
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">
                {t.settings.openaiApiKey}
                {status?.vision.openai_api_key_masked && (
                  <span className="ml-2 text-green-600 font-normal">
                    {status.vision.openai_api_key_masked}
                  </span>
                )}
              </label>
              <input
                type="password"
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                placeholder={hasOpenaiKey ? t.settings.keyMasked : t.settings.apiKeyPlaceholder}
                className={`w-full rounded border border-gray-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400 ${
                  hasOpenaiKey && !openaiKey ? "bg-green-50 placeholder:text-green-500" : "placeholder:text-gray-400"
                }`}
              />
              <p className="mt-1 text-xs text-gray-400">{t.settings.openaiApiKeyHint}</p>
            </div>
          )}

          {/* Model */}
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600">{t.settings.openaiVisionModel}</label>
            <select
              value={openaiModel}
              onChange={(e) => setOpenaiModel(e.target.value)}
              className="w-full rounded border border-gray-200 px-2 py-2 text-sm focus:border-blue-400 focus:outline-none"
            >
              <option value="gpt-4o-mini">gpt-4o-mini</option>
              <option value="gpt-4o">gpt-4o</option>
              <option value="gpt-4-turbo">gpt-4-turbo</option>
            </select>
          </div>

          {/* Vision actions */}
          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={handleTestVision}
              disabled={testingVision}
              className={`rounded px-4 py-2 text-xs font-medium text-white transition ${
                testingVision ? "cursor-not-allowed bg-gray-300" : "bg-teal-600 hover:bg-teal-700"
              }`}
            >
              {testingVision ? t.settings.testing : t.settings.testVision}
            </button>
            <button
              type="button"
              onClick={() => handleClearKey("openai")}
              className="rounded border border-red-200 px-4 py-2 text-xs font-medium text-red-600 hover:bg-red-50 transition"
            >
              {t.settings.clearKey}
            </button>
          </div>
          {visionTestResult && (
            <div
              className={`rounded border px-3 py-2 text-xs ${
                visionTestResult.ok
                  ? "border-green-200 bg-green-50 text-green-700"
                  : "border-red-200 bg-red-50 text-red-700"
              }`}
            >
              {visionTestResult.text}
            </div>
          )}
        </div>
      </section>

      {/* ── V1.8: Data Management ─────────────────────────────────────── */}
      <DataManagementSection />

      {/* ── Security Notice ──────────────────────────────────────────── */}
      <section className="rounded border border-blue-200 bg-blue-50 p-4 text-xs text-blue-800">
        <p className="font-medium mb-1">🔒 安全说明</p>
        <p>{t.settings.securityNotice}</p>
      </section>

      {/* ── Save ─────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className={`rounded px-6 py-2 text-sm font-medium text-white transition ${
            saving ? "cursor-not-allowed bg-gray-300" : "bg-blue-600 hover:bg-blue-700 active:bg-blue-800"
          }`}
        >
          {saving ? t.settings.saving : t.settings.save}
        </button>
        {saveMsg && (
          <span
            className={`text-xs ${saveMsg.ok ? "text-green-600" : "text-red-500"}`}
          >
            {saveMsg.text}
          </span>
        )}
      </div>
    </div>
  );
}

/* ── V1.8: Data Management Section ──────────────────────────────────── */

function DataManagementSection() {
  const [exporting, setExporting] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<Record<string, unknown> | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  const handleExport = async () => {
    setExporting(true);
    try {
      const res = await fetch(`${BASE}/export`);
      if (!res.ok) throw new Error("导出失败");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "aesthetic-backup.zip";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert("导出失败，请确认后端服务正常运行。");
    } finally {
      setExporting(false);
    }
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    setImportError(null);
    setImportResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${BASE}/import`, { method: "POST", body: fd });
      const data = await res.json();
      if (res.ok) {
        setImportResult(data);
      } else {
        setImportError(data.detail || "导入失败");
      }
    } catch {
      setImportError("导入失败，请确认后端服务正常运行。");
    } finally {
      setImporting(false);
      // Reset file input
      e.target.value = "";
    }
  };

  return (
    <section className="rounded border bg-white p-5 shadow-sm">
      <h3 className="text-base font-semibold text-gray-700 mb-4">数据管理</h3>

      {/* Export */}
      <div className="mb-4 pb-4 border-b">
        <p className="text-sm text-gray-600 mb-2">导出备份包</p>
        <p className="text-xs text-gray-400 mb-3">
          导出训练记录、参考案例、上传图片和配置摘要（不含 API Key）。可用于备份或迁移到新电脑。
        </p>
        <button
          onClick={handleExport}
          disabled={exporting}
          className={`rounded px-4 py-2 text-xs font-medium text-white transition ${
            exporting ? "cursor-not-allowed bg-gray-300" : "bg-teal-600 hover:bg-teal-700"
          }`}
        >
          {exporting ? "导出中…" : "导出备份包 (.zip)"}
        </button>
      </div>

      {/* Import */}
      <div>
        <p className="text-sm text-gray-600 mb-2">导入备份包</p>
        <p className="text-xs text-gray-400 mb-3">
          上传之前导出的 .zip 备份包。第一版为「合并导入」，不会清空当前数据。导入的图片和案例 ID 会自动重映射，不会覆盖现有数据。
        </p>
        <label className={`inline-block rounded px-4 py-2 text-xs font-medium text-white transition cursor-pointer ${
          importing ? "bg-gray-300 cursor-not-allowed" : "bg-indigo-600 hover:bg-indigo-700"
        }`}>
          {importing ? "导入中…" : "上传并导入"}
          <input
            type="file"
            accept=".zip"
            onChange={handleImport}
            disabled={importing}
            className="hidden"
          />
        </label>

        {importError && (
          <div className="mt-3 rounded border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
            {importError}
          </div>
        )}
        {importResult && (
          <div className="mt-3 rounded border border-green-200 bg-green-50 px-3 py-2 text-xs text-green-700 space-y-1">
            <p className="font-medium">导入完成</p>
            <p>参考案例：{String(importResult.reference_cases_imported || 0)}</p>
            <p>训练记录：{String(importResult.sessions_imported || 0)}</p>
            <p>图片：{String(importResult.images_imported || 0)}</p>
            <p>跳过：{String(importResult.skipped_items || 0)}</p>
            {Array.isArray(importResult.warnings) && (importResult.warnings as string[]).length > 0 && (
              <div className="mt-1">
                <p className="font-medium">警告：</p>
                {(importResult.warnings as string[]).map((w, i) => (
                  <p key={i} className="text-amber-600">{w}</p>
                ))}
              </div>
            )}
          </div>
        )}
        <p className="mt-2 text-xs text-gray-400">
          导入后，如需语义搜索请前往参考案例库点击「重建语义索引」。
        </p>
      </div>
    </section>
  );
}
