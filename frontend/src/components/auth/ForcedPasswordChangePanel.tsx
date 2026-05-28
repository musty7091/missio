import { Eye, EyeOff, KeyRound, Loader2, LockKeyhole, LogOut, Moon, ShieldCheck, Sun } from "lucide-react"
import type { FormEvent } from "react"
import { useState } from "react"
import { useTranslation } from "../../i18n/language"
import { getCurrentUser } from "../../services/authService"
import { ApiError } from "../../services/httpClient"
import { changeOwnPassword } from "../../services/profileSecurityService"
import type { UserMeResponse } from "../../types/auth"
import type { ThemeMode } from "../../types/task"

type ForcedPasswordChangePanelProps = {
  user: UserMeResponse
  theme: ThemeMode
  onToggleTheme: () => void
  onLogout: () => void
  onPasswordChanged: (user: UserMeResponse) => void
}

function getErrorMessage(error: unknown, fallbackMessage: string) {
  if (error instanceof ApiError) {
    if (typeof error.message === "string" && error.message.trim()) {
      return error.message
    }
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message
  }

  return fallbackMessage
}

export function ForcedPasswordChangePanel({
  user,
  theme,
  onToggleTheme,
  onLogout,
  onPasswordChanged,
}: ForcedPasswordChangePanelProps) {
  const { t } = useTranslation()
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [newPasswordRepeat, setNewPasswordRepeat] = useState("")
  const [showPasswords, setShowPasswords] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!currentPassword || !newPassword || !newPasswordRepeat) {
      setErrorMessage(t("forcedPassword.error.required"))
      return
    }

    if (newPassword !== newPasswordRepeat) {
      setErrorMessage(t("forcedPassword.error.mismatch"))
      return
    }

    setIsSubmitting(true)
    setErrorMessage(null)
    setSuccessMessage(null)

    try {
      await changeOwnPassword({
        current_password: currentPassword,
        new_password: newPassword,
        new_password_repeat: newPasswordRepeat,
      })

      const refreshedUser = await getCurrentUser()
      setSuccessMessage(t("forcedPassword.success"))
      onPasswordChanged(refreshedUser)
    } catch (error) {
      setErrorMessage(getErrorMessage(error, t("forcedPassword.error.default")))
    } finally {
      setIsSubmitting(false)
    }
  }

  const passwordVisibilityLabel = showPasswords
    ? t("forcedPassword.hidePasswords")
    : t("forcedPassword.showPasswords")

  return (
    <main className="min-h-screen bg-[var(--missio-page-bg)] px-4 py-5 text-[var(--missio-text-main)] transition-colors duration-300">
      <section className="mx-auto flex min-h-[calc(100vh-40px)] w-full max-w-md flex-col">
        <header className="mb-5 flex items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="text-2xl font-black tracking-tight">Missio</p>
            <p className="mt-1 text-sm font-bold text-cyan-500">{t("forcedPassword.headerSubtitle")}</p>
          </div>

          <button
            type="button"
            onClick={onToggleTheme}
            className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm transition active:scale-95"
            aria-label={t("forcedPassword.themeToggle")}
            title={t("forcedPassword.themeToggle")}
          >
            {theme === "light" ? <Moon size={20} /> : <Sun size={20} />}
          </button>
        </header>

        <section className="rounded-[1.8rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-5 shadow-xl shadow-slate-900/5">
          <div className="mb-5 flex items-start gap-3">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200">
              <ShieldCheck size={25} />
            </div>

            <div className="min-w-0">
              <p className="text-[0.68rem] font-black uppercase tracking-[0.18em] text-cyan-600 dark:text-cyan-300">
                {t("forcedPassword.eyebrow")}
              </p>
              <h1 className="mt-1 text-2xl font-black tracking-tight">
                {t("forcedPassword.title")}
              </h1>
              <p className="mt-2 text-sm font-bold leading-6 text-[var(--missio-text-muted)]">
                {t("forcedPassword.description").replace("{name}", user.full_name)}
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-3.5">
            <label className="block">
              <span className="mb-1.5 block text-sm font-black">{t("forcedPassword.currentPassword")}</span>
              <div className="flex items-center gap-3 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3">
                <LockKeyhole size={19} className="text-[var(--missio-text-muted)]" />
                <input
                  value={currentPassword}
                  onChange={(event) => setCurrentPassword(event.target.value)}
                  type={showPasswords ? "text" : "password"}
                  autoComplete="current-password"
                  className="min-w-0 flex-1 bg-transparent text-sm font-semibold outline-none"
                  placeholder={t("forcedPassword.currentPasswordPlaceholder")}
                />
              </div>
            </label>

            <label className="block">
              <span className="mb-1.5 block text-sm font-black">{t("forcedPassword.newPassword")}</span>
              <div className="flex items-center gap-3 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3">
                <KeyRound size={19} className="text-[var(--missio-text-muted)]" />
                <input
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  type={showPasswords ? "text" : "password"}
                  autoComplete="new-password"
                  className="min-w-0 flex-1 bg-transparent text-sm font-semibold outline-none"
                  placeholder={t("forcedPassword.newPasswordPlaceholder")}
                />
              </div>
            </label>

            <label className="block">
              <span className="mb-1.5 block text-sm font-black">{t("forcedPassword.newPasswordRepeat")}</span>
              <div className="flex items-center gap-3 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3">
                <KeyRound size={19} className="text-[var(--missio-text-muted)]" />
                <input
                  value={newPasswordRepeat}
                  onChange={(event) => setNewPasswordRepeat(event.target.value)}
                  type={showPasswords ? "text" : "password"}
                  autoComplete="new-password"
                  className="min-w-0 flex-1 bg-transparent text-sm font-semibold outline-none"
                  placeholder={t("forcedPassword.newPasswordRepeatPlaceholder")}
                />

                <button
                  type="button"
                  onClick={() => setShowPasswords((currentValue) => !currentValue)}
                  className="rounded-xl p-1 text-[var(--missio-text-muted)]"
                  aria-label={passwordVisibilityLabel}
                  title={passwordVisibilityLabel}
                >
                  {showPasswords ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </label>

            <div className="rounded-2xl border border-cyan-200 bg-cyan-50 p-3 text-xs font-bold leading-5 text-cyan-900 dark:border-cyan-900 dark:bg-cyan-950/30 dark:text-cyan-100">
              {t("forcedPassword.info")}
            </div>

            {errorMessage && (
              <p className="rounded-2xl border border-red-200 bg-red-50 px-3 py-2 text-sm font-bold text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-100">
                {errorMessage}
              </p>
            )}

            {successMessage && (
              <p className="rounded-2xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-bold text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-100">
                {successMessage}
              </p>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-cyan-600 px-4 text-sm font-black text-white shadow-lg shadow-cyan-900/15 transition active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-70"
            >
              {isSubmitting ? <Loader2 className="animate-spin" size={18} /> : <ShieldCheck size={18} />}
              {t("forcedPassword.submit")}
            </button>

            <button
              type="button"
              onClick={onLogout}
              className="flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 text-sm font-black text-[var(--missio-text-main)]"
            >
              <LogOut size={18} />
              {t("forcedPassword.logout")}
            </button>
          </form>
        </section>
      </section>
    </main>
  )
}
