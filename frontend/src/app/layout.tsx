"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Fraunces } from "next/font/google";
import { I18nProvider, useT } from "@/i18n";
import "./globals.css";

const fraunces = Fraunces({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  style: ["normal", "italic"],
  variable: "--font-fraunces",
  display: "swap",
});

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

const NAV = [
  { href: "/", zh: "工作台", en: "Workbench" },
  { href: "/assessment", zh: "训练评估", en: "Assessment" },
  { href: "/audit", zh: "案例库体检", en: "Audit" },
  { href: "/help", zh: "帮助", en: "Help" },
  { href: "/settings", zh: "设置", en: "Settings" },
];

function Header() {
  const { t, lang, setLang } = useT();
  const pathname = usePathname();
  const toggle = () => setLang(lang === "en" ? "zh" : "en");

  return (
    <header className="sticky top-0 z-40 border-b border-line/70 bg-paper/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-4xl flex-wrap items-center justify-between gap-x-4 gap-y-2 px-5 py-3">
        {/* Wordmark — a small ink "seal" + the title */}
        <Link href="/" className="group flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-[7px] bg-ink text-surface shadow-soft transition-transform group-hover:-rotate-3">
            <span className="font-display text-[15px] italic leading-none">Æ</span>
          </span>
          <span className="flex flex-col leading-tight">
            <span className="text-[15px] font-semibold tracking-tightish text-ink">{t.app.title}</span>
            <span className="font-display text-[10px] italic tracking-wide text-muted">Aesthetic Atelier</span>
          </span>
        </Link>

        <div className="flex items-center gap-1.5">
          <nav className="flex items-center gap-0.5">
            {NAV.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`relative px-2.5 py-1.5 text-[13px] font-medium transition-colors ${
                    active ? "text-ink" : "text-muted hover:text-ink-soft"
                  }`}
                >
                  {lang === "en" ? item.en : item.zh}
                  {active && (
                    <span className="absolute inset-x-2.5 -bottom-px h-[1.5px] rounded-full bg-accent" />
                  )}
                </Link>
              );
            })}
          </nav>
          <button
            onClick={toggle}
            className="ml-1 rounded-full border border-line bg-surface px-3 py-1 text-[11px] font-medium tracking-wide text-ink-soft transition hover:border-accent/40 hover:text-accent"
            title={lang === "en" ? "切换到中文" : "Switch to English"}
          >
            {lang === "en" ? "中文" : "EN"}
          </button>
        </div>
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
    <html lang="zh-CN" className={fraunces.variable}>
      <body className="min-h-screen font-sans">
        <I18nProvider>
          <Header />
          <main className="reveal mx-auto max-w-4xl px-5 py-9">{children}</main>
        </I18nProvider>
      </body>
    </html>
  );
}
