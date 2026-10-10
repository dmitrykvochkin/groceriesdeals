"use client";

export type Language = "nl" | "en";

export function LanguageSwitch({
  language,
  onChange,
}: {
  language: Language;
  onChange: (language: Language) => void;
}) {
  return (
    <div className="languageSwitch" aria-label={language === "nl" ? "Kies taal" : "Choose language"}>
      <button
        className={language === "nl" ? "active" : ""}
        type="button"
        aria-pressed={language === "nl"}
        onClick={() => onChange("nl")}
      >
        NL
      </button>
      <button
        className={language === "en" ? "active" : ""}
        type="button"
        aria-pressed={language === "en"}
        onClick={() => onChange("en")}
      >
        EN
      </button>
    </div>
  );
}
