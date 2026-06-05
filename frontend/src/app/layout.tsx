"use client";

import { I18nProvider, useT } from "@/i18n";
import type { Lang } from "@/i18n";
import "./globals.css";

function Header() {
  const { t, lang, setLang } = useT();

  const toggle = () => setLang(lang === "en" ? "zh" : "en");

  return (
    <header className="border-b bg-white">
      <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
        <h1 className="text-lg font-semibold tracking-tight">
          {t.app.title}
        </h1>
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
