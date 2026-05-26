import { useTranslation, type AppLanguage } from "../../i18n/language"

export function LanguageSelector() {
  const { language, setLanguage, t } = useTranslation()

  function handleLanguageChange(nextLanguage: AppLanguage) {
    setLanguage(nextLanguage)
  }

  return (
    <div
      className="inline-flex h-10 shrink-0 items-center rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-1 shadow-sm"
      aria-label={t("language.selector")}
      title={t("language.selector")}
    >
      <button
        type="button"
        onClick={() => handleLanguageChange("tr")}
        className={
          language === "tr"
            ? "flex h-8 items-center gap-1.5 rounded-xl bg-[var(--missio-primary)] px-3 text-xs font-black text-white"
            : "flex h-8 items-center gap-1.5 rounded-xl px-3 text-xs font-black text-[var(--missio-text-muted)]"
        }
      >
        <span aria-hidden="true">🇹🇷</span>
        <span>{t("language.turkish")}</span>
      </button>

      <button
        type="button"
        onClick={() => handleLanguageChange("en")}
        className={
          language === "en"
            ? "flex h-8 items-center gap-1.5 rounded-xl bg-[var(--missio-primary)] px-3 text-xs font-black text-white"
            : "flex h-8 items-center gap-1.5 rounded-xl px-3 text-xs font-black text-[var(--missio-text-muted)]"
        }
      >
        <span aria-hidden="true">🇬🇧</span>
        <span>{t("language.english")}</span>
      </button>
    </div>
  )
}
