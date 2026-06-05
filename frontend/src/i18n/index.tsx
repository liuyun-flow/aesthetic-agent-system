"use client";

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import en from "./en";
import zh from "./zh";

export type Lang = "en" | "zh";
export type Translations = typeof en;

const translations: Record<Lang, Translations> = { en, zh };

const LANG_KEY = "aesthetic-lang";

function detectLang(): Lang {
  if (typeof window === "undefined") return "zh";
  const stored = localStorage.getItem(LANG_KEY);
  if (stored === "zh" || stored === "en") return stored;
  // Default to Chinese
  return "zh";
}

interface I18nContextValue {
  lang: Lang;
  t: Translations;
  setLang: (lang: Lang) => void;
}

const I18nContext = createContext<I18nContextValue>({
  lang: "en",
  t: en,
  setLang: () => {},
});

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(detectLang);

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    localStorage.setItem(LANG_KEY, l);
  }, []);

  return (
    <I18nContext.Provider value={{ lang, t: translations[lang], setLang }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useT() {
  return useContext(I18nContext);
}
