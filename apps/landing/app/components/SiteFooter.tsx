import Link from "next/link";
import { Brand } from "./Brand";
import {
  PRIVACY_PATH,
  PRODUCT_NAME,
  SUPPORT_PATH,
  TERMS_PATH,
} from "../constants";
import type { Language } from "./LanguageSwitch";

const copy = {
  nl: {
    footerLine: "Actuele supermarktdeals, gewoon in je chat.",
    disclaimer:
      "Onafhankelijke ChatGPT-app. Niet gelieerd aan Picnic, Albert Heijn of Jumbo.",
    privacy: "Privacy",
    terms: "Voorwaarden",
    support: "Support",
    backToTop: "Naar boven",
  },
  en: {
    footerLine: "Current supermarket deals, right in your chat.",
    disclaimer:
      "Independent ChatGPT app. Not affiliated with Picnic, Albert Heijn, or Jumbo.",
    privacy: "Privacy",
    terms: "Terms",
    support: "Support",
    backToTop: "Back to top",
  },
} as const;

export function SiteFooter({
  language,
  homeHref = "/",
  showBackToTop = true,
}: {
  language: Language;
  homeHref?: string;
  showBackToTop?: boolean;
}) {
  const t = copy[language];

  return (
    <footer>
      <div className="container footerTop">
        <Brand href={homeHref} />
        <p>{t.footerLine}</p>
        {showBackToTop ? (
          <a href="#top">
            {t.backToTop}
            <span aria-hidden="true">↑</span>
          </a>
        ) : (
          <span />
        )}
      </div>
      <div className="container footerLinks">
        <Link href={PRIVACY_PATH}>{t.privacy}</Link>
        <Link href={TERMS_PATH}>{t.terms}</Link>
        <Link href={SUPPORT_PATH}>{t.support}</Link>
      </div>
      <div className="container footerBottom">
        <span>
          © {new Date().getFullYear()} {PRODUCT_NAME}
        </span>
        <span>{t.disclaimer}</span>
      </div>
    </footer>
  );
}
