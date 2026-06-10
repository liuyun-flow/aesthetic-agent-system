"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { I18nProvider, useT } from "@/i18n";
import type { Lang } from "@/i18n";
import "./globals.css";

// ── V2.1.2+: Global chunk-load error recovery ───────────────────────────

const CHUNK_RELOAD_KEY = "_aesthetic_chunk_reloaded";

function attachChunkErrorHandler() {
  if (typeof window === "undefined") return;
  // Only register once across the app lifecycle
  if ((window as any).__aesthetic_chunk_handler_installed) return;
  (window as any).__aesthetic_chunk_handler_installed = true;

  window.addEventListener("unhandledrejection", (event) => {
    const msg = String(event.reason?.message || event.reason || "");
    const isChunkError =
      msg.includes("ChunkLoadError") ||
      msg.includes("Loading chunk") ||
      msg.includes("Failed to fetch dynamically imported module") ||
      msg.includes("error loading dynamically imported module");
    if (!isChunkError) return;

    event.preventDefault();
    const alreadyReloaded = sessionStorage.getItem(CHUNK_RELOAD_KEY);
    if (alreadyReloaded) {
      // Second failure — show manual recovery instructions
      document.body.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:center;min-height:100vh;font-family:sans-serif">
          <div style="text-align:center;max-width:400px;padding:2rem">
            <h2 style="font-size:1.25rem;font-weight:600;color:#dc2626;margin-bottom:0.5rem">
              页面资源更新失败
            </h2>
            <p style="font-size:0.875rem;color:#6b7280;margin-bottom:1rem">
              自动刷新未能解决问题，请尝试以下任一方法：
            </p>
            <ul style="text-align:left;font-size:0.8rem;color:#4b5563;line-height:1.8">
              <li>按 <strong>Ctrl+F5</strong> 强制刷新页面</li>
              <li>打开浏览器设置 → 清除最近一小时的缓存</li>
              <li>重启前端服务：<code>docker compose restart frontend</code></li>
            </ul>
          </div>
        </div>`;
    } else {
      sessionStorage.setItem(CHUNK_RELOAD_KEY, "1");
      window.location.reload();
    }
  });
}

function Header() {
  const { t, lang, setLang } = useT();
  const pathname = usePathname();

  const toggle = () => setLang(lang === "en" ? "zh" : "en");

  return (
    <header className="border-b bg-white">
      <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold tracking-tight">
            {t.app.title}
          </h1>
          <Link
            href="/"
            className={`rounded px-2 py-1 text-xs font-medium transition ${
              pathname === "/"
                ? "bg-blue-50 text-blue-600"
                : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
            }`}
          >
            {lang === "en" ? "Workbench" : "工作台"}
          </Link>
          <Link
            href="/settings"
            className={`rounded px-2 py-1 text-xs font-medium transition ${
              pathname === "/settings"
                ? "bg-blue-50 text-blue-600"
                : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
            }`}
          >
            {lang === "en" ? "Settings" : "设置"}
          </Link>
          <Link
            href="/help"
            className={`rounded px-2 py-1 text-xs font-medium transition ${
              pathname === "/help"
                ? "bg-blue-50 text-blue-600"
                : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
            }`}
          >
            {lang === "en" ? "Help" : "帮助"}
          </Link>
          <Link
            href="/audit"
            className={`rounded px-2 py-1 text-xs font-medium transition ${
              pathname === "/audit"
                ? "bg-blue-50 text-blue-600"
                : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
            }`}
          >
            {lang === "en" ? "Audit" : "案例库体检"}
          </Link>
          <Link
            href="/assessment"
            className={`rounded px-2 py-1 text-xs font-medium transition ${
              pathname === "/assessment"
                ? "bg-blue-50 text-blue-600"
                : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
            }`}
          >
            {lang === "en" ? "Assessment" : "训练评估"}
          </Link>
        </div>
        <button
          onClick={toggle}
          className="rounded border border-gray-200 px-3 py-1 text-xs font-medium text-gray-600
                     hover:bg-gray-100 transition"
          title={lang === "en" ? "Switch to Chinese" : "切换到英文"}
        >
          {lang === "en" ? "中文" : "EN"}
        </button>
      </div>
    </header>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  useEffect(() => { attachChunkErrorHandler(); }, []);

  return (
    <html lang="en">
      <body className="min-h-screen">
        <I18nProvider>
          <Header />
          <main className="mx-auto max-w-4xl px-4 py-6">{children}</main>
        </I18nProvider>
      </body>
    </html>
  );
}
