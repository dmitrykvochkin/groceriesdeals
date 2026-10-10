"use client";

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";
import { Brand } from "./Brand";
import { LanguageSwitch, type Language } from "./LanguageSwitch";
import { SiteFooter } from "./SiteFooter";

const navCopy = {
  nl: {
    home: "Home",
    how: "Zo werkt het",
    faq: "Veelgestelde vragen",
  },
  en: {
    home: "Home",
    how: "How it works",
    faq: "FAQ",
  },
} as const;

export function LegalShell({
  title,
  updated,
  nl,
  en,
}: {
  title: Record<Language, string>;
  updated: Record<Language, string>;
  nl: ReactNode;
  en: ReactNode;
}) {
  const [language, setLanguage] = useState<Language>("nl");
  const nav = navCopy[language];

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  return (
    <main id="top" className="legalPage">
      <header className="siteHeader legalHeader">
        <div className="container navInner">
          <Brand />
          <nav className="desktopNav" aria-label={language === "nl" ? "Hoofdnavigatie" : "Main navigation"}>
            <Link href="/">{nav.home}</Link>
            <Link href="/#how">{nav.how}</Link>
            <Link href="/#faq">{nav.faq}</Link>
          </nav>
          <div className="navActions">
            <LanguageSwitch language={language} onChange={setLanguage} />
          </div>
        </div>
      </header>

      <section className="legalHero">
        <div className="container">
          <p className="eyebrow">
            <span>✦</span>
            {language === "nl" ? "Juridisch" : "Legal"}
          </p>
          <h1>{title[language]}</h1>
          <p className="legalUpdated">{updated[language]}</p>
        </div>
      </section>

      <section className="legalBody">
        <div className="container legalContent">{language === "nl" ? nl : en}</div>
      </section>

      <SiteFooter language={language} showBackToTop />
    </main>
  );
}
