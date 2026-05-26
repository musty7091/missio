import { LogOut, Moon, Sun } from "lucide-react"
import { useTranslation, type TranslationKey } from "../../i18n/language"
import type { ThemeMode } from "../../types/task"

type AppHeaderProps = {
  theme: ThemeMode
  displayName: string
  role: string
  onToggleTheme: () => void
  onLogout: () => void
}

function getRoleLabel(
  role: string,
  t: (key: TranslationKey) => string,
) {
  if (role === "boss") return t("role.boss")
  if (role === "super_admin") return t("role.super_admin")
  if (role === "manager") return t("role.manager")
  if (role === "staff") return t("role.staff")

  return role
}

function MissioMiniLogo() {
  return (
    <div className="relative flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-cyan-300/30 bg-cyan-400/10 shadow-xl shadow-cyan-500/10">
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-cyan-300/30 via-blue-500/10 to-transparent" />
      <div className="relative h-7 w-8">
        <div className="absolute left-0 top-1 h-6 w-2 rounded-sm bg-cyan-300" />
        <div className="absolute left-2 top-0 h-7 w-2 rotate-[-38deg] rounded-sm bg-cyan-400" />
        <div className="absolute right-2 top-0 h-7 w-2 rotate-[38deg] rounded-sm bg-blue-500" />
        <div className="absolute right-0 top-1 h-6 w-2 rounded-sm bg-blue-600" />
        <div className="absolute right-[-3px] top-[-6px] h-2.5 w-2.5 rounded-full bg-cyan-300" />
      </div>
    </div>
  )
}

export function AppHeader({
  theme,
  displayName,
  role,
  onToggleTheme,
  onLogout,
}: AppHeaderProps) {
  const { t } = useTranslation()

  return (
    <header className="mb-5 rounded-[2rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-xl shadow-slate-900/5">
      <div className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <MissioMiniLogo />

          <div className="min-w-0">
            <div className="flex min-w-0 items-center gap-2">
              <p className="shrink-0 text-lg font-black leading-none tracking-tight">
                Missio
              </p>

              <span className="max-w-[7rem] truncate rounded-full bg-[var(--missio-primary-soft)] px-2.5 py-1 text-[0.65rem] font-black text-cyan-700 dark:text-cyan-200">
                {getRoleLabel(role, t)}
              </span>
            </div>

            <p className="mt-1 truncate text-sm font-bold text-[var(--missio-text-muted)]">
              {t("header.greeting")}, {displayName}
            </p>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <button
            type="button"
            onClick={onToggleTheme}
            className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-3 text-[var(--missio-text-main)] shadow-sm transition active:scale-95"
            aria-label={t("theme.toggle")}
            title={t("theme.toggle")}
          >
            {theme === "light" ? <Moon size={19} /> : <Sun size={19} />}
          </button>

          <button
            type="button"
            onClick={onLogout}
            className="rounded-2xl border border-red-200 bg-red-50 p-3 text-red-600 shadow-sm transition active:scale-95 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
            aria-label={t("header.logout")}
            title={t("header.logout")}
          >
            <LogOut size={19} />
          </button>
        </div>
      </div>
    </header>
  )
}
