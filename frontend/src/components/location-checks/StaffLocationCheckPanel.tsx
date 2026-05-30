import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  Loader2,
  MapPin,
  RefreshCw,
  ShieldAlert,
} from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslation, type AppLanguage } from "../../i18n/language"
import {
  failLocationCheck,
  listMyPendingLocationChecks,
  markLocationCheckSeen,
  shareLocationCheck,
} from "../../services/locationCheckService"
import {
  getBrowserLocationPayload,
  getLocationErrorMessage,
  mapLocationErrorToCode,
} from "../../services/browserLocationService"
import type { LocationCheck } from "../../types/locationCheck"

type StaffLocationCheckPanelProps = {
  onChanged?: () => void
  silentLoading?: boolean
}

type ActionMessage = {
  tone: "success" | "error" | "warning"
  text: string
}

type StaffPanelTexts = {
  authorizedUser: string
  notificationSent: string
  notificationPartialFailed: string
  notificationNoSubscription: string
  notificationFailed: string
  notificationConfigurationError: string
  notificationPending: string
  loadError: string
  shareSuccess: string
  shareErrorPermissionDenied: string
  shareErrorPositionUnavailable: string
  shareErrorTimeout: string
  shareErrorUnsupported: string
  shareErrorDefault: string
  loadingTitle: string
  loadingDescription: string
  badge: string
  title: string
  description: string
  refreshAria: string
  errorTitle: string
  resultTitle: string
  requestedAt: string
  statusSeen: string
  statusWaiting: string
  gettingLocation: string
  shareButton: string
}

const staffPanelTexts: Record<AppLanguage, StaffPanelTexts> = {
  tr: {
    authorizedUser: "Yetkili kullanıcı",
    notificationSent: "Bildirim gönderildi",
    notificationPartialFailed: "Bildirim kısmen gönderildi",
    notificationNoSubscription: "Cihaz bildirime kayıtlı değil",
    notificationFailed: "Bildirim gönderilemedi",
    notificationConfigurationError: "Bildirim ayarı eksik",
    notificationPending: "Bildirim beklemede",
    loadError: "Konum yoklama istekleri alınamadı.",
    shareSuccess: "Konumun başarıyla paylaşıldı.",
    shareErrorPermissionDenied: "Konum izni kapalı. Tarayıcı veya cihaz ayarlarından konum iznini açmalısın.",
    shareErrorPositionUnavailable: "Konum bilgisi alınamadı. Lütfen konum servislerini kontrol et.",
    shareErrorTimeout: "Konum alınırken zaman aşımı oldu. Lütfen tekrar dene.",
    shareErrorUnsupported: "Bu cihaz veya tarayıcı konum paylaşımını desteklemiyor.",
    shareErrorDefault: "Konum paylaşılamadı. Lütfen tekrar dene.",
    loadingTitle: "Konum yoklaması kontrol ediliyor",
    loadingDescription: "Bekleyen konum istekleri hazırlanıyor.",
    badge: "Konum yoklaması",
    title: "Bekleyen konum isteği",
    description: "Yetkili kişi konumunu paylaşmanı istiyor.",
    refreshAria: "Konum yoklamalarını yenile",
    errorTitle: "Konum istekleri alınamadı",
    resultTitle: "İşlem sonucu",
    requestedAt: "İstek zamanı",
    statusSeen: "Görüldü",
    statusWaiting: "Bekliyor",
    gettingLocation: "Konum alınıyor",
    shareButton: "Konumumu Paylaş",
  },
  en: {
    authorizedUser: "Authorized user",
    notificationSent: "Notification sent",
    notificationPartialFailed: "Notification partially sent",
    notificationNoSubscription: "Device is not registered for notifications",
    notificationFailed: "Notification could not be sent",
    notificationConfigurationError: "Notification configuration missing",
    notificationPending: "Notification pending",
    loadError: "Location check requests could not be loaded.",
    shareSuccess: "Your location has been shared successfully.",
    shareErrorPermissionDenied: "Location permission is disabled. Enable location permission from your browser or device settings.",
    shareErrorPositionUnavailable: "Location information could not be retrieved. Please check location services.",
    shareErrorTimeout: "Location request timed out. Please try again.",
    shareErrorUnsupported: "This device or browser does not support location sharing.",
    shareErrorDefault: "Location could not be shared. Please try again.",
    loadingTitle: "Checking location requests",
    loadingDescription: "Preparing pending location requests.",
    badge: "Location check",
    title: "Pending location request",
    description: "An authorized user is asking you to share your location.",
    refreshAria: "Refresh location checks",
    errorTitle: "Location requests could not be loaded",
    resultTitle: "Action result",
    requestedAt: "Requested at",
    statusSeen: "Seen",
    statusWaiting: "Waiting",
    gettingLocation: "Getting location",
    shareButton: "Share My Location",
  },
}

function formatDateTime(value: string | null, language: AppLanguage) {
  if (!value) {
    return "-"
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return "-"
  }

  return date.toLocaleString(language === "tr" ? "tr-TR" : "en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function getRequestSourceLabel(check: LocationCheck, texts: StaffPanelTexts) {
  if (check.requested_by_user_full_name) {
    return check.requested_by_user_full_name
  }

  return texts.authorizedUser
}

function getNotificationLabel(check: LocationCheck, texts: StaffPanelTexts) {
  if (check.notification_status === "sent") {
    return texts.notificationSent
  }

  if (check.notification_status === "partial_failed") {
    return texts.notificationPartialFailed
  }

  if (check.notification_status === "no_subscription") {
    return texts.notificationNoSubscription
  }

  if (check.notification_status === "failed") {
    return texts.notificationFailed
  }

  if (check.notification_status === "configuration_error") {
    return texts.notificationConfigurationError
  }

  return texts.notificationPending
}

function getActionMessageClass(tone: ActionMessage["tone"]) {
  if (tone === "success") {
    return "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-100"
  }

  if (tone === "warning") {
    return "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-100"
  }

  return "border-red-200 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950/30 dark:text-red-100"
}

function getShareFailureMessage(errorCode: string, texts: StaffPanelTexts) {
  if (errorCode === "permission_denied") {
    return texts.shareErrorPermissionDenied
  }

  if (errorCode === "position_unavailable") {
    return texts.shareErrorPositionUnavailable
  }

  if (errorCode === "timeout") {
    return texts.shareErrorTimeout
  }

  if (errorCode === "unsupported") {
    return texts.shareErrorUnsupported
  }

  return texts.shareErrorDefault
}

export function StaffLocationCheckPanel({ onChanged, silentLoading = false }: StaffLocationCheckPanelProps) {
  const { language } = useTranslation()
  const texts = staffPanelTexts[language]

  const [checks, setChecks] = useState<LocationCheck[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [actionMessage, setActionMessage] = useState<ActionMessage | null>(null)
  const [busyCheckId, setBusyCheckId] = useState<number | null>(null)
  const [seenMarkedIds, setSeenMarkedIds] = useState<Set<number>>(() => new Set())

  const pendingCount = useMemo(() => checks.length, [checks])

  const loadPendingChecks = useCallback(
    async (showLoading: boolean) => {
      if (showLoading) {
        setIsLoading(true)
      } else {
        setIsRefreshing(true)
      }

      setErrorMessage(null)

      try {
        const response = await listMyPendingLocationChecks()
        setChecks(response.checks)
      } catch {
        setErrorMessage(texts.loadError)
      } finally {
        setIsLoading(false)
        setIsRefreshing(false)
      }
    },
    [texts.loadError],
  )

  useEffect(() => {
    void loadPendingChecks(true)
  }, [loadPendingChecks])

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      if (document.visibilityState === "visible") {
        void loadPendingChecks(false)
      }
    }, 15000)

    const handleFocus = () => {
      void loadPendingChecks(false)
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        void loadPendingChecks(false)
      }
    }

    window.addEventListener("focus", handleFocus)
    document.addEventListener("visibilitychange", handleVisibilityChange)

    return () => {
      window.clearInterval(intervalId)
      window.removeEventListener("focus", handleFocus)
      document.removeEventListener("visibilitychange", handleVisibilityChange)
    }
  }, [loadPendingChecks])

  useEffect(() => {
    const pendingSeenIds = checks
      .filter((check) => check.status === "pending" && !seenMarkedIds.has(check.id))
      .map((check) => check.id)

    if (pendingSeenIds.length === 0) {
      return
    }

    setSeenMarkedIds((currentIds) => {
      const nextIds = new Set(currentIds)

      pendingSeenIds.forEach((id) => {
        nextIds.add(id)
      })

      return nextIds
    })

    void Promise.all(
      pendingSeenIds.map((id) =>
        markLocationCheckSeen(id).catch((error) => {
          console.warn("MISSIO_LOCATION_CHECK_SEEN_MARK_FAILED", {
            locationCheckId: id,
            error,
          })
        }),
      ),
    ).then(() => {
      void loadPendingChecks(false)
    })
  }, [checks, loadPendingChecks, seenMarkedIds])

  async function handleShareLocation(check: LocationCheck) {
    setBusyCheckId(check.id)
    setActionMessage(null)
    setErrorMessage(null)

    try {
      const locationPayload = await getBrowserLocationPayload()

      await shareLocationCheck(check.id, {
        latitude: locationPayload.latitude,
        longitude: locationPayload.longitude,
        location_accuracy: locationPayload.location_accuracy,
      })

      setActionMessage({
        tone: "success",
        text: texts.shareSuccess,
      })

      await loadPendingChecks(false)
      onChanged?.()
    } catch (error) {
      const responseErrorCode = mapLocationErrorToCode(error)
      const responseErrorMessage = getLocationErrorMessage(error)

      try {
        await failLocationCheck(check.id, {
          response_error_code: responseErrorCode,
          response_error_message: responseErrorMessage,
        })
      } catch (failError) {
        console.warn("MISSIO_LOCATION_CHECK_FAIL_SAVE_FAILED", failError)
      }

      setActionMessage({
        tone: responseErrorCode === "permission_denied" ? "warning" : "error",
        text: getShareFailureMessage(responseErrorCode, texts),
      })

      await loadPendingChecks(false)
      onChanged?.()
    } finally {
      setBusyCheckId(null)
    }
  }

  if (isLoading) {
    if (silentLoading) {
      return null
    }

    return (
      <section className="rounded-[1.75rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
            <Loader2 className="animate-spin" size={21} />
          </div>

          <div>
            <p className="text-sm font-black">{texts.loadingTitle}</p>
            <p className="mt-1 text-xs font-semibold text-[var(--missio-text-muted)]">
              {texts.loadingDescription}
            </p>
          </div>
        </div>
      </section>
    )
  }

  if (!errorMessage && pendingCount === 0 && !actionMessage) {
    return null
  }

  return (
    <section className="rounded-[1.75rem] border border-cyan-200 bg-cyan-50/80 p-4 shadow-sm dark:border-cyan-900 dark:bg-cyan-950/25">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-cyan-100 text-cyan-700 dark:bg-cyan-900 dark:text-cyan-100">
            <MapPin size={22} />
          </div>

          <div>
            <p className="text-[0.68rem] font-black uppercase tracking-[0.16em] text-cyan-700 dark:text-cyan-200">
              {texts.badge}
            </p>
            <h2 className="mt-1 text-base font-black text-slate-950 dark:text-white">
              {texts.title}
            </h2>
            <p className="mt-1 text-xs font-bold leading-5 text-slate-700 dark:text-slate-200">
              {texts.description}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => void loadPendingChecks(false)}
          disabled={isRefreshing}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-white/80 text-cyan-700 shadow-sm transition active:scale-95 disabled:cursor-wait disabled:opacity-60 dark:bg-slate-900 dark:text-cyan-100"
          aria-label={texts.refreshAria}
        >
          {isRefreshing ? <Loader2 className="animate-spin" size={18} /> : <RefreshCw size={18} />}
        </button>
      </div>

      {errorMessage && (
        <div className="mb-3 rounded-2xl border border-red-200 bg-red-50 p-3 text-xs font-bold leading-5 text-red-800 dark:border-red-900 dark:bg-red-950/30 dark:text-red-100">
          <div className="mb-1 flex items-center gap-2 font-black">
            <AlertCircle size={16} />
            {texts.errorTitle}
          </div>
          {errorMessage}
        </div>
      )}

      {actionMessage && (
        <div className={`mb-3 rounded-2xl border p-3 text-xs font-bold leading-5 ${getActionMessageClass(actionMessage.tone)}`}>
          <div className="mb-1 flex items-center gap-2 font-black">
            {actionMessage.tone === "success" ? <CheckCircle2 size={16} /> : <ShieldAlert size={16} />}
            {texts.resultTitle}
          </div>
          {actionMessage.text}
        </div>
      )}

      {checks.length > 0 && (
        <div className="space-y-3">
          {checks.map((check) => (
            <article
              key={check.id}
              className="rounded-[1.35rem] border border-white/70 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-950/70"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-black text-slate-950 dark:text-white">
                    {getRequestSourceLabel(check, texts)}
                  </p>
                  <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
                    {texts.requestedAt}: {formatDateTime(check.requested_at_utc, language)}
                  </p>
                </div>

                <span className="rounded-full bg-cyan-100 px-2.5 py-1 text-[0.65rem] font-black text-cyan-700 dark:bg-cyan-950 dark:text-cyan-100">
                  {check.status === "seen" ? texts.statusSeen : texts.statusWaiting}
                </span>
              </div>

              {check.request_note && (
                <p className="mt-3 rounded-2xl bg-slate-50 p-3 text-xs font-bold leading-5 text-slate-700 dark:bg-slate-900 dark:text-slate-200">
                  {check.request_note}
                </p>
              )}

              <div className="mt-3 flex flex-wrap items-center gap-2 text-[0.7rem] font-bold text-[var(--missio-text-muted)]">
                <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 dark:bg-slate-900">
                  <Clock3 size={12} />
                  {getNotificationLabel(check, texts)}
                </span>
              </div>

              <button
                type="button"
                onClick={() => void handleShareLocation(check)}
                disabled={busyCheckId === check.id}
                className="mt-3 flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-cyan-600 px-4 text-sm font-black text-white shadow-lg shadow-cyan-500/20 transition active:scale-95 disabled:cursor-wait disabled:opacity-70"
              >
                {busyCheckId === check.id ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    {texts.gettingLocation}
                  </>
                ) : (
                  <>
                    <MapPin size={18} />
                    {texts.shareButton}
                  </>
                )}
              </button>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
