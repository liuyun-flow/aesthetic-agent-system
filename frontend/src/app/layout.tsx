"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { I18nProvider, useT } from "@/i18n";
import type { Lang } from "@/i18n";
import "./globals.css";

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
