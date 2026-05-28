import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  KeyRound,
  Loader2,
  RefreshCw,
  ShieldCheck,
} from "lucide-react"
import { useEffect, useState } from "react"
import { useTranslation, type AppLanguage } from "../../i18n/language"
import {
  listPasswordResetRequests,
  resetPasswordResetRequest,
  type PasswordResetRequestItem,
} from "../../services/passwordResetRequestService"

type PanelTexts = {
  title: string
  description: string
  badge: string
  refresh: string
  loading: string
  emptyTitle: string
  emptyDescription: string
  requestedBy: string
  username: string
  role: string
  requestedAt: string
  resetButton: string
  resetting: string
  temporaryPasswordTitle: string
  temporaryPasswordDescription: string
  copyInfo: string
  confirmReset: string
  resetSuccess: string
  loadError: string
  resetError: string
  staff: string
  manager: string
  boss: string
  superAdmin: string
  unknownRole: string
}

const panelTexts: Record<AppLanguage, PanelTexts> = {
  tr: {
    title: "\u015eifre s\u0131f\u0131rlama talepleri",
    description:
      "Personel veya y\u00f6netici \u015fifresini unuttu\u011funda olu\u015fan bekleyen talepler burada g\u00f6r\u00fcn\u00fcr.",
    badge: "G\u00fcvenlik",
    refresh: "Yenile",
    loading: "Talepler y\u00fckleniyor...",
    emptyTitle: "Bekleyen talep yok",
    emptyDescription: "\u015eifre s\u0131f\u0131rlama talebi geldi\u011finde burada g\u00f6r\u00fcnecek.",
    requestedBy: "Talep sahibi",
    username: "Kullan\u0131c\u0131 ad\u0131",
    role: "Rol",
    requestedAt: "Talep zaman\u0131",
    resetButton: "\u015eifreyi s\u0131f\u0131rla",
    resetting: "S\u0131f\u0131rlan\u0131yor...",
    temporaryPasswordTitle: "Ge\u00e7ici \u015fifre olu\u015fturuldu",
    temporaryPasswordDescription:
      "Bu \u015fifreyi kullan\u0131c\u0131ya ilet. Kullan\u0131c\u0131 ilk giri\u015fte kendi yeni \u015fifresini belirleyecek.",
    copyInfo: "Ge\u00e7ici \u015fifre ekranda sadece bu i\u015flem sonucunda g\u00f6sterilir.",
    confirmReset: "{name} kullan\u0131c\u0131s\u0131 i\u00e7in ge\u00e7ici \u015fifre olu\u015fturulsun mu?",
    resetSuccess: "Ge\u00e7ici \u015fifre olu\u015fturuldu.",
    loadError: "\u015eifre talepleri al\u0131namad\u0131.",
    resetError: "\u015eifre s\u0131f\u0131rlanamad\u0131.",
    staff: "Personel",
    manager: "Y\u00f6netici",
    boss: "\u0130\u015fletme Sahibi",
    superAdmin: "S\u00fcper Admin",
    unknownRole: "Bilinmeyen rol",
  },
  en: {
    title: "Password reset requests",
    description:
      "Pending requests created when a staff member or manager forgets their password appear here.",
    badge: "Security",
    refresh: "Refresh",
    loading: "Loading requests...",
    emptyTitle: "No pending requests",
    emptyDescription: "Password reset requests will appear here when they are created.",
    requestedBy: "Requested by",
    username: "Username",
    role: "Role",
    requestedAt: "Requested at",
    resetButton: "Reset password",
    resetting: "Resetting...",
    temporaryPasswordTitle: "Temporary password created",
    temporaryPasswordDescription:
      "Share this password with the user. The user will set their own new password on first login.",
    copyInfo: "The temporary password is shown only as the result of this action.",
    confirmReset: "Create a temporary password for {name}?",
    resetSuccess: "Temporary password created.",
    loadError: "Password reset requests could not be loaded.",
    resetError: "Password could not be reset.",
    staff: "Staff",
    manager: "Manager",
    boss: "Owner",
    superAdmin: "Super Admin",
    unknownRole: "Unknown role",
  },
}

function getRoleLabel(role: string, texts: PanelTexts) {
  if (role === "staff") {
    return texts.staff
  }

  if (role === "manager") {
    return texts.manager
  }

  if (role === "boss") {
    return texts.boss
  }

  if (role === "super_admin") {
    return texts.superAdmin
  }

  return texts.unknownRole
}

function formatDate(value: string, language: AppLanguage) {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleString(language === "en" ? "en-GB" : "tr-TR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export function PasswordResetRequestsPanel() {
  const { language } = useTranslation()
  const texts = panelTexts[language]

  const [requests, setRequests] = useState<PasswordResetRequestItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [busyRequestId, setBusyRequestId] = useState<number | null>(null)
  const [temporaryPassword, setTemporaryPassword] = useState("")
  const [temporaryPasswordUsername, setTemporaryPasswordUsername] = useState("")
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  async function loadRequests() {
    setIsLoading(true)
    setErrorMessage(null)

    try {
      const response = await listPasswordResetRequests("pending")
      setRequests(response)
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage(texts.loadError)
      }
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadRequests()
  }, [language])

  async function handleResetPassword(resetRequest: PasswordResetRequestItem) {
    const confirmed = window.confirm(
      texts.confirmReset.replace("{name}", resetRequest.target_full_name),
    )

    if (!confirmed) {
      return
    }

    setBusyRequestId(resetRequest.id)
    setStatusMessage(null)
    setErrorMessage(null)
    setTemporaryPassword("")
    setTemporaryPasswordUsername("")

    try {
      const response = await resetPasswordResetRequest(resetRequest.id)

      setTemporaryPassword(response.temporary_password)
      setTemporaryPasswordUsername(response.target_username)
      setStatusMessage(texts.resetSuccess)
      await loadRequests()
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage(texts.resetError)
      }
    } finally {
      setBusyRequestId(null)
    }
  }

  return (
    <div className="rounded-[2rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-xl shadow-slate-900/5">
      <div className="flex items-start gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200">
          <ShieldCheck size={22} />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-cyan-50 px-3 py-1 text-[0.65rem] font-black uppercase tracking-[0.14em] text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200">
              {texts.badge}
            </span>
            {requests.length > 0 && (
              <span className="rounded-full bg-red-50 px-3 py-1 text-xs font-black text-red-700 dark:bg-red-950 dark:text-red-200">
                {requests.length}
              </span>
            )}
          </div>

          <h3 className="mt-2 text-lg font-black tracking-tight">{texts.title}</h3>
          <p className="mt-1 text-sm font-semibold leading-6 text-[var(--missio-text-muted)]">
            {texts.description}
          </p>
        </div>
      </div>

      {statusMessage && (
        <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
          {statusMessage}
        </div>
      )}

      {errorMessage && (
        <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
          {errorMessage}
        </div>
      )}

      {temporaryPassword && (
        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
          <div className="flex items-start gap-3">
            <CheckCircle2 size={22} className="mt-0.5 shrink-0" />
            <div className="min-w-0 flex-1">
              <h4 className="text-sm font-black">{texts.temporaryPasswordTitle}</h4>
              <p className="mt-1 text-xs font-bold leading-5">
                {texts.temporaryPasswordDescription}
              </p>

              <div className="mt-3 rounded-2xl border border-amber-200 bg-white/80 px-4 py-3 dark:border-amber-800 dark:bg-slate-950/40">
                <p className="text-xs font-black uppercase tracking-[0.12em]">
                  {temporaryPasswordUsername}
                </p>
                <p className="mt-1 break-all text-lg font-black tracking-wide">
                  {temporaryPassword}
                </p>
              </div>

              <p className="mt-2 text-xs font-bold leading-5 opacity-80">
                {texts.copyInfo}
              </p>
            </div>
          </div>
        </div>
      )}

      <button
        type="button"
        onClick={() => void loadRequests()}
        disabled={isLoading || busyRequestId !== null}
        className="mt-4 flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 text-sm font-black text-[var(--missio-text-main)] transition active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isLoading ? <Loader2 className="animate-spin" size={18} /> : <RefreshCw size={18} />}
        {isLoading ? texts.loading : texts.refresh}
      </button>

      <div className="mt-4 space-y-3">
        {!isLoading && requests.length === 0 && (
          <div className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-4">
            <div className="flex items-start gap-3">
              <AlertCircle size={21} className="mt-0.5 shrink-0 text-[var(--missio-text-muted)]" />
              <div>
                <h4 className="text-sm font-black">{texts.emptyTitle}</h4>
                <p className="mt-1 text-xs font-bold leading-5 text-[var(--missio-text-muted)]">
                  {texts.emptyDescription}
                </p>
              </div>
            </div>
          </div>
        )}

        {requests.map((resetRequest) => (
          <article
            key={resetRequest.id}
            className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-4"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs font-black uppercase tracking-[0.12em] text-[var(--missio-text-muted)]">
                  {texts.requestedBy}
                </p>
                <h4 className="mt-1 text-base font-black">
                  {resetRequest.target_full_name}
                </h4>
                <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
                  {texts.username}: {resetRequest.requested_username}
                </p>
              </div>

              <span className="shrink-0 rounded-full bg-[var(--missio-primary-soft)] px-3 py-1 text-xs font-black text-cyan-700 dark:text-cyan-200">
                {getRoleLabel(resetRequest.target_role, texts)}
              </span>
            </div>

            <div className="mt-3 flex items-center gap-2 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-3 py-2 text-xs font-bold text-[var(--missio-text-muted)]">
              <Clock3 size={15} />
              {texts.requestedAt}: {formatDate(resetRequest.requested_at_utc, language)}
            </div>

            <button
              type="button"
              onClick={() => void handleResetPassword(resetRequest)}
              disabled={busyRequestId !== null}
              className="mt-3 flex min-h-11 w-full items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 text-sm font-black text-white shadow-lg shadow-teal-500/20 transition active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {busyRequestId === resetRequest.id ? (
                <Loader2 className="animate-spin" size={18} />
              ) : (
                <KeyRound size={18} />
              )}
              {busyRequestId === resetRequest.id ? texts.resetting : texts.resetButton}
            </button>
          </article>
        ))}
      </div>
    </div>
  )
}
