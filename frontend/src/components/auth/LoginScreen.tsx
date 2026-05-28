import {
  AlertCircle,
  Building2,
  Camera,
  ClipboardCheck,
  Eye,
  EyeOff,
  Loader2,
  LockKeyhole,
  LogIn,
  MapPin,
  Moon,
  ShieldCheck,
  Sun,
  User,
} from "lucide-react"
import type { FormEvent, ReactNode } from "react"
import { useState } from "react"
import { LanguageSelector } from "../language/LanguageSelector"
import { getCurrentUser, loginUser, requestForgotPassword } from "../../services/authService"
import { setAccessToken } from "../../services/authTokenStorage"
import { ApiError } from "../../services/httpClient"
import type { UserMeResponse } from "../../types/auth"
import type { ThemeMode } from "../../types/task"
import { useTranslation, type TranslationKey } from "../../i18n/language"

type LoginScreenProps = {
  theme: ThemeMode
  onToggleTheme: () => void
  onLoginSuccess: (user: UserMeResponse) => void
}

type LoginInputProps = {
  label: string
  value: string
  placeholder: string
  autoComplete: string
  icon: ReactNode
  type?: string
  autoCapitalize?: string
  spellCheck?: boolean
  rightElement?: ReactNode
  onChange: (value: string) => void
}

function LoginInput({
  label,
  value,
  placeholder,
  autoComplete,
  icon,
  type = "text",
  autoCapitalize,
  spellCheck,
  rightElement,
  onChange,
}: LoginInputProps) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-black text-[var(--missio-text-main)]">
        {label}
      </span>

      <div className="flex items-center gap-3 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3 shadow-inner shadow-slate-900/[0.02] transition focus-within:border-[var(--missio-primary)] focus-within:ring-4 focus-within:ring-cyan-500/10">
        <div className="text-[var(--missio-text-muted)]">{icon}</div>

        <input
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="min-w-0 flex-1 bg-transparent text-sm font-semibold text-[var(--missio-text-main)] outline-none placeholder:text-[var(--missio-text-muted)]"
          placeholder={placeholder}
          autoComplete={autoComplete}
          autoCapitalize={autoCapitalize}
          spellCheck={spellCheck}
          type={type}
        />

        {rightElement}
      </div>
    </label>
  )
}

function MissioLogoMark() {
  return (
    <div className="relative flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan-300/30 bg-cyan-400/10 shadow-xl shadow-cyan-500/10">
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

function getReadableLoginErrorMessage(
  error: unknown,
  t: (key: TranslationKey) => string,
) {
  if (error instanceof ApiError) {
    if (error.status === 0) {
      return t("login.error.serverUnavailable")
    }

    if (error.status === 401) {
      return t("login.error.invalidCredentials")
    }

    if (error.status === 403) {
      return error.message || t("login.error.forbidden")
    }

    if (error.status === 429) {
      return t("login.error.tooManyAttempts")
    }

    if (error.status >= 500) {
      return t("login.error.serverError")
    }

    return error.message || t("login.error.failed")
  }

  if (error instanceof Error) {
    return error.message
  }

  return t("login.error.failed")
}

export function LoginScreen({ theme, onToggleTheme, onLoginSuccess }: LoginScreenProps) {
  const { t } = useTranslation()
  const [businessSlug, setBusinessSlug] = useState("")
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isForgotPasswordOpen, setIsForgotPasswordOpen] = useState(false)
  const [isForgotPasswordSubmitting, setIsForgotPasswordSubmitting] = useState(false)
  const [forgotPasswordMessage, setForgotPasswordMessage] = useState<string | null>(null)

  function clearErrorMessage() {
    if (errorMessage) {
      setErrorMessage(null)
    }
  }

  function handleBusinessSlugChange(value: string) {
    clearErrorMessage()
    setBusinessSlug(value)
  }

  function handleUsernameChange(value: string) {
    clearErrorMessage()
    setUsername(value)
  }

  function handlePasswordChange(value: string) {
    clearErrorMessage()
    setPassword(value)
  }

  async function handleForgotPasswordRequest() {
    const cleanBusinessSlug = businessSlug.trim().toLowerCase()
    const cleanUsername = username.trim()

    if (!cleanBusinessSlug || !cleanUsername) {
      setForgotPasswordMessage(t("login.forgotPasswordRequired"))
      return
    }

    setIsForgotPasswordSubmitting(true)
    setForgotPasswordMessage(null)

    try {
      await requestForgotPassword({
        business_slug: cleanBusinessSlug,
        username: cleanUsername,
      })

      setForgotPasswordMessage(t("login.forgotPasswordSuccess"))
    } catch {
      setForgotPasswordMessage(t("login.forgotPasswordFailed"))
    } finally {
      setIsForgotPasswordSubmitting(false)
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const cleanBusinessSlug = businessSlug.trim().toLowerCase()
    const cleanUsername = username.trim()

    if (!cleanUsername) {
      setErrorMessage(t("login.error.usernameRequired"))
      return
    }

    if (!password) {
      setErrorMessage(t("login.error.passwordRequired"))
      return
    }

    setErrorMessage(null)
    setIsSubmitting(true)

    try {
      const tokenResponse = await loginUser({
        business_slug: cleanBusinessSlug || undefined,
        username: cleanUsername,
        password,
      })

      setAccessToken(tokenResponse.access_token)

      const currentUser = await getCurrentUser()
      onLoginSuccess(currentUser)
    } catch (error) {
      setErrorMessage(getReadableLoginErrorMessage(error, t))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="min-h-screen overflow-hidden bg-[var(--missio-page-bg)] text-[var(--missio-text-main)] transition-colors duration-300">
      <section className="relative mx-auto flex min-h-screen w-full max-w-md flex-col px-4 py-4">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-56 bg-gradient-to-b from-cyan-500/20 via-blue-500/10 to-transparent blur-3xl dark:from-cyan-400/20" />
        <div className="pointer-events-none absolute -right-24 top-16 h-44 w-44 rounded-full bg-cyan-400/20 blur-3xl" />

        <header className="relative z-10 flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <MissioLogoMark />

            <div className="min-w-0">
              <p
                className="truncate text-[1.55rem] leading-none tracking-tight text-[var(--missio-text-main)]"
                style={{ fontWeight: 900 }}
              >
                Missio
              </p>
              <p className="mt-1 truncate text-sm font-bold tracking-wide text-cyan-500">
                Mission is possible...
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onToggleTheme}
            className="shrink-0 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm transition active:scale-95"
            aria-label={t("theme.toggle")}
            title={t("theme.toggle")}
          >
            {theme === "light" ? <Moon size={20} /> : <Sun size={20} />}
          </button>
        </header>

        <div className="relative z-10 mt-3 flex justify-end">
          <LanguageSelector />
        </div>

        <section className="relative z-10 mt-3 overflow-hidden rounded-[1.8rem] border border-cyan-300/20 bg-slate-950 p-4 text-white shadow-xl shadow-cyan-950/20">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(34,211,238,0.24),transparent_32%),linear-gradient(135deg,rgba(15,23,42,1),rgba(2,6,23,1))]" />
          <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full border border-cyan-300/20" />
          <div className="absolute right-7 top-16 h-3 w-3 rounded-full bg-cyan-300 shadow-lg shadow-cyan-300/50" />

          <div className="relative">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-1.5 text-[0.7rem] font-black text-cyan-200">
              <ShieldCheck size={13} />
              {t("login.heroBadge")}
            </div>

            <h1 className="text-xl font-black leading-tight tracking-tight min-[380px]:text-[1.35rem]">
              {t("login.heroTitleStart")}{" "}
              <span className="text-cyan-300">{t("login.heroTitleMiddle")}</span>{" "}
              {t("login.heroTitleEnd")}
            </h1>

            <div className="mt-4 grid grid-cols-3 gap-2">
              <div className="rounded-2xl border border-white/10 bg-white/10 p-2.5 backdrop-blur">
                <ClipboardCheck className="mb-1.5 text-cyan-300" size={18} />
                <p className="text-[0.68rem] font-black leading-4">
                  {t("login.featureTaskTracking")}
                </p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/10 p-2.5 backdrop-blur">
                <Camera className="mb-1.5 text-cyan-300" size={18} />
                <p className="text-[0.68rem] font-black leading-4">
                  {t("login.featurePhotoProof")}
                </p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/10 p-2.5 backdrop-blur">
                <MapPin className="mb-1.5 text-cyan-300" size={18} />
                <p className="text-[0.68rem] font-black leading-4">
                  {t("login.featureLocationRecord")}
                </p>
              </div>
            </div>
          </div>
        </section>

        <form
          onSubmit={handleSubmit}
          className="relative z-10 mt-4 rounded-[1.8rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-xl shadow-slate-900/5"
        >
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-black tracking-tight">{t("login.title")}</h2>
              <p className="mt-1 text-sm font-medium leading-5 text-[var(--missio-text-muted)]">
                {t("login.description")}
              </p>
            </div>

            <div className="rounded-2xl bg-[var(--missio-primary-soft)] p-3 text-cyan-700 dark:text-cyan-200">
              <ShieldCheck size={22} />
            </div>
          </div>

          <div className="space-y-3.5">
            <LoginInput
              label={t("login.businessCode")}
              value={businessSlug}
              onChange={handleBusinessSlugChange}
              placeholder={t("login.businessCodePlaceholder")}
              autoComplete="organization"
              autoCapitalize="none"
              spellCheck={false}
              icon={<Building2 size={19} />}
            />

            <LoginInput
              label={t("login.username")}
              value={username}
              onChange={handleUsernameChange}
              placeholder={t("login.usernamePlaceholder")}
              autoComplete="username"
              autoCapitalize="none"
              spellCheck={false}
              icon={<User size={19} />}
            />

            <LoginInput
              label={t("login.password")}
              value={password}
              onChange={handlePasswordChange}
              placeholder={t("login.passwordPlaceholder")}
              autoComplete="current-password"
              autoCapitalize="none"
              spellCheck={false}
              type={showPassword ? "text" : "password"}
              icon={<LockKeyhole size={19} />}
              rightElement={
                <button
                  type="button"
                  onClick={() => setShowPassword((currentValue) => !currentValue)}
                  className="rounded-xl p-1 text-[var(--missio-text-muted)] transition hover:text-[var(--missio-text-main)]"
                  aria-label={showPassword ? t("login.hidePassword") : t("login.showPassword")}
                  title={showPassword ? t("login.hidePassword") : t("login.showPassword")}
                >
                  {showPassword ? <EyeOff size={19} /> : <Eye size={19} />}
                </button>
              }
            />
          </div>

          {errorMessage && (
            <div className="mt-4 flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold leading-5 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
              <AlertCircle className="mt-0.5 shrink-0" size={18} />
              <p>{errorMessage}</p>
            </div>
          )}
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
              <button
                type="button"
                onClick={() => {
                  setIsForgotPasswordOpen((currentValue) => !currentValue)
                  setForgotPasswordMessage(null)
                }}
                className="text-sm font-bold text-cyan-400 transition hover:text-cyan-300"
              >
                {t("login.forgotPassword")}
              </button>

              {isForgotPasswordOpen ? (
                <div className="mt-3 space-y-3">
                  <p className="text-xs font-medium leading-5 text-[var(--missio-text-muted)]">
                    {t("login.forgotPasswordDescription")}
                  </p>

                  <button
                    type="button"
                    onClick={handleForgotPasswordRequest}
                    disabled={isForgotPasswordSubmitting}
                    className="w-full rounded-xl bg-cyan-500 px-4 py-2 text-sm font-black text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                {isForgotPasswordSubmitting
                  ? t("login.forgotPasswordSubmitting")
                  : t("login.forgotPasswordSubmit")}
              </button>

                  {forgotPasswordMessage ? (
                    <p className="rounded-xl border border-cyan-400/30 bg-cyan-400/10 px-3 py-2 text-xs font-semibold leading-5 text-[var(--missio-text-main)]">
                      {forgotPasswordMessage}
                    </p>
                  ) : null}
                </div>
              ) : null}
            </div>
          <button type="submit"
            disabled={isSubmitting}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 py-4 text-sm font-black text-white shadow-lg shadow-teal-500/20 transition active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="animate-spin" size={19} />
                {t("login.submitting")}
              </>
            ) : (
              <>
                <LogIn size={19} />
                {t("login.submit")}
              </>
            )}
          </button>
        </form>
      </section>
    </main>
  )
}
