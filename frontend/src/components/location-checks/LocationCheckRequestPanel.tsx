import {
  AlertCircle,
  BellRing,
  CheckCircle2,
  Clock3,
  Loader2,
  MapPin,
  RefreshCw,
  Send,
  ShieldAlert,
  UsersRound,
} from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslation, type AppLanguage } from "../../i18n/language"
import {
  listBusinessUsers,
  type BusinessUser,
} from "../../services/businessUserService"
import {
  createLocationCheck,
  listLocationChecks,
} from "../../services/locationCheckService"
import type { LocationCheck } from "../../types/locationCheck"

type LocationCheckRequestPanelProps = {
  businessId: number | null
  allowedTargetRoles?: string[]
}

type PanelMessage = {
  tone: "success" | "error" | "warning"
  text: string
}

type RequestPanelTexts = {
  badge: string
  title: string
  description: string
  refreshAria: string
  resultTitle: string
  staffLabel: string
  staffSelectPlaceholder: string
  allEligibleStaff: string
  noteLabel: string
  notePlaceholder: string
  sending: string
  sendButton: string
  recentTitle: string
  emptyRecent: string
  responsePrefix: string
  latitude: string
  longitude: string
  openMap: string
  userFallbackPrefix: string
  noBusiness: string
  selectStaff: string
  noEligibleStaff: string
  loadError: string
  createError: string
  requestCreated: string
  requestCreatedWithMissingNotifications: string
  statusPending: string
  statusSeen: string
  statusShared: string
  statusPermissionDenied: string
  statusFailed: string
  statusExpired: string
  statusCancelled: string
  notificationSent: string
  notificationPartialFailed: string
  notificationNoSubscription: string
  notificationFailed: string
  notificationConfigurationError: string
  notificationPending: string
}

const requestPanelTexts: Record<AppLanguage, RequestPanelTexts> = {
  tr: {
    badge: "Konum yoklama",
    title: "Personelden konum iste",
    description: "Personel uygulamayı açtığında bekleyen konum isteğini görür.",
    refreshAria: "Konum yoklama panelini yenile",
    resultTitle: "İşlem sonucu",
    staffLabel: "Personel",
    staffSelectPlaceholder: "Personel seç",
    allEligibleStaff: "Tüm uygun personeller",
    noteLabel: "Not",
    notePlaceholder: "Örn: Depo çıkışı öncesi konum paylaş.",
    sending: "İstek gönderiliyor",
    sendButton: "Konum İste",
    recentTitle: "Son yoklamalar",
    emptyRecent: "Henüz konum yoklaması oluşturulmadı.",
    responsePrefix: "Yanıt",
    latitude: "Enlem",
    longitude: "Boylam",
    openMap: "Haritada Aç",
    userFallbackPrefix: "Kullanıcı",
    noBusiness: "İşletme bilgisi bulunamadı.",
    selectStaff: "Konum istemek için personel seçmelisin.",
    noEligibleStaff: "Konum istenebilecek aktif personel bulunamadı.",
    loadError: "Konum yoklama bilgileri alınamadı.",
    createError: "Konum isteği oluşturulamadı.",
    requestCreated: "{created} konum isteği oluşturuldu.",
    requestCreatedWithMissingNotifications:
      "{created} konum isteği oluşturuldu. {missing} kişide bildirim kaydı yok; istek yine de uygulama içinde bekleyecek.",
    statusPending: "Bekleniyor",
    statusSeen: "Görüldü",
    statusShared: "Konum paylaşıldı",
    statusPermissionDenied: "Konum izni kapalı",
    statusFailed: "Başarısız",
    statusExpired: "Süre doldu",
    statusCancelled: "İptal",
    notificationSent: "Bildirim gönderildi",
    notificationPartialFailed: "Bildirim kısmen gönderildi",
    notificationNoSubscription: "Cihaz bildirime kayıtlı değil",
    notificationFailed: "Bildirim başarısız",
    notificationConfigurationError: "Bildirim ayarı eksik",
    notificationPending: "Bildirim beklemede",
  },
  en: {
    badge: "Location check",
    title: "Request staff location",
    description: "When the staff member opens the app, they will see the pending location request.",
    refreshAria: "Refresh location check panel",
    resultTitle: "Action result",
    staffLabel: "Staff",
    staffSelectPlaceholder: "Select staff",
    allEligibleStaff: "All eligible staff",
    noteLabel: "Note",
    notePlaceholder: "Example: Share location before leaving the warehouse.",
    sending: "Sending request",
    sendButton: "Request Location",
    recentTitle: "Recent checks",
    emptyRecent: "No location check has been created yet.",
    responsePrefix: "Response",
    latitude: "Latitude",
    longitude: "Longitude",
    openMap: "Open in Maps",
    userFallbackPrefix: "User",
    noBusiness: "Business information was not found.",
    selectStaff: "Select a staff member to request location.",
    noEligibleStaff: "No active eligible staff member was found.",
    loadError: "Location check information could not be loaded.",
    createError: "Location request could not be created.",
    requestCreated: "{created} location request was created.",
    requestCreatedWithMissingNotifications:
      "{created} location request was created. {missing} user(s) do not have a notification subscription; the request will still wait inside the app.",
    statusPending: "Waiting",
    statusSeen: "Seen",
    statusShared: "Location shared",
    statusPermissionDenied: "Location permission disabled",
    statusFailed: "Failed",
    statusExpired: "Expired",
    statusCancelled: "Cancelled",
    notificationSent: "Notification sent",
    notificationPartialFailed: "Notification partially sent",
    notificationNoSubscription: "Device is not registered for notifications",
    notificationFailed: "Notification failed",
    notificationConfigurationError: "Notification configuration missing",
    notificationPending: "Notification pending",
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

function getStatusLabel(check: LocationCheck, texts: RequestPanelTexts) {
  if (check.status === "pending") return texts.statusPending
  if (check.status === "seen") return texts.statusSeen
  if (check.status === "shared") return texts.statusShared
  if (check.status === "permission_denied") return texts.statusPermissionDenied
  if (check.status === "failed") return texts.statusFailed
  if (check.status === "expired") return texts.statusExpired
  if (check.status === "cancelled") return texts.statusCancelled

  return check.status
}

function getStatusClass(check: LocationCheck) {
  if (check.status === "shared") {
    return "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200"
  }

  if (check.status === "permission_denied" || check.status === "failed") {
    return "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-200"
  }

  if (check.status === "seen") {
    return "bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200"
  }

  return "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-200"
}

function getNotificationLabel(check: LocationCheck, texts: RequestPanelTexts) {
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

function buildGoogleMapsUrl(check: LocationCheck) {
  if (check.latitude === null || check.longitude === null) {
    return null
  }

  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
    `${check.latitude},${check.longitude}`,
  )}`
}

function formatCoordinate(value: number | null) {
  if (value === null) {
    return "-"
  }

  return value.toFixed(6)
}

function getMessageClass(tone: PanelMessage["tone"]) {
  if (tone === "success") {
    return "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-100"
  }

  if (tone === "warning") {
    return "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-100"
  }

  return "border-red-200 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950/30 dark:text-red-100"
}

function getUserLabel(user: BusinessUser) {
  return `${user.full_name} @${user.username}`
}

function replaceMessageVariables(template: string, values: Record<string, number | string>) {
  return Object.entries(values).reduce(
    (currentText, [key, value]) => currentText.replace(`{${key}}`, String(value)),
    template,
  )
}

export function LocationCheckRequestPanel({
  businessId,
  allowedTargetRoles = ["manager", "staff"],
}: LocationCheckRequestPanelProps) {
  const { language } = useTranslation()
  const texts = requestPanelTexts[language]

  const [users, setUsers] = useState<BusinessUser[]>([])
  const [checks, setChecks] = useState<LocationCheck[]>([])
  const [selectedUserId, setSelectedUserId] = useState<number | "all" | "">("")
  const [requestNote, setRequestNote] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [message, setMessage] = useState<PanelMessage | null>(null)

  const targetUsers = useMemo(
    () =>
      users.filter(
        (user) =>
          user.is_active &&
          allowedTargetRoles.includes(user.role) &&
          user.role !== "boss",
      ),
    [allowedTargetRoles, users],
  )

  const recentChecks = useMemo(() => checks.slice(0, 6), [checks])

  const loadPanelData = useCallback(
    async (showLoading = true) => {
      if (!businessId) {
        setUsers([])
        setChecks([])
        return
      }

      if (showLoading) {
        setIsLoading(true)
      }

      try {
        const [usersResponse, checksResponse] = await Promise.all([
          listBusinessUsers(businessId),
          listLocationChecks({
            businessId,
            limit: 20,
            offset: 0,
          }),
        ])

        setUsers(usersResponse)
        setChecks(checksResponse.checks)
      } catch {
        setMessage({
          tone: "error",
          text: texts.loadError,
        })
      } finally {
        setIsLoading(false)
      }
    },
    [businessId, texts.loadError],
  )

  useEffect(() => {
    void loadPanelData(true)
  }, [loadPanelData])

  useEffect(() => {
    if (!businessId) {
      return
    }

    function refreshWhenVisible() {
      if (document.visibilityState === "visible") {
        void loadPanelData(false)
      }
    }

    const intervalId = window.setInterval(refreshWhenVisible, 15000)

    window.addEventListener("focus", refreshWhenVisible)
    document.addEventListener("visibilitychange", refreshWhenVisible)

    return () => {
      window.clearInterval(intervalId)
      window.removeEventListener("focus", refreshWhenVisible)
      document.removeEventListener("visibilitychange", refreshWhenVisible)
    }
  }, [businessId, loadPanelData])

  async function handleRequestLocation() {
    if (!businessId) {
      setMessage({
        tone: "error",
        text: texts.noBusiness,
      })
      return
    }

    if (!selectedUserId) {
      setMessage({
        tone: "warning",
        text: texts.selectStaff,
      })
      return
    }

    const selectedTargetIds =
      selectedUserId === "all"
        ? targetUsers.map((user) => user.id)
        : [Number(selectedUserId)]

    if (selectedTargetIds.length === 0) {
      setMessage({
        tone: "warning",
        text: texts.noEligibleStaff,
      })
      return
    }

    setIsSending(true)
    setMessage(null)

    try {
      const response = await createLocationCheck(
        {
          target_user_ids: selectedTargetIds,
          request_note: requestNote.trim() || null,
        },
        businessId,
      )

      const noSubscriptionCount = response.checks.filter(
        (check) => check.notification_status === "no_subscription",
      ).length

      setMessage({
        tone: noSubscriptionCount > 0 ? "warning" : "success",
        text:
          noSubscriptionCount > 0
            ? replaceMessageVariables(texts.requestCreatedWithMissingNotifications, {
                created: response.created_count,
                missing: noSubscriptionCount,
              })
            : replaceMessageVariables(texts.requestCreated, {
                created: response.created_count,
              }),
      })

      setRequestNote("")
      setSelectedUserId("")
      await loadPanelData(false)
    } catch {
      setMessage({
        tone: "error",
        text: texts.createError,
      })
    } finally {
      setIsSending(false)
    }
  }

  return (
    <section className="rounded-[1.7rem] border border-cyan-200 bg-cyan-50/70 p-3 shadow-sm dark:border-cyan-900 dark:bg-cyan-950/20">
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
          onClick={() => void loadPanelData(false)}
          disabled={isLoading}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-white/80 text-cyan-700 shadow-sm transition active:scale-95 disabled:cursor-wait disabled:opacity-60 dark:bg-slate-900 dark:text-cyan-100"
          aria-label={texts.refreshAria}
        >
          {isLoading ? <Loader2 className="animate-spin" size={18} /> : <RefreshCw size={18} />}
        </button>
      </div>

      {message && (
        <div className={`mb-3 rounded-2xl border p-3 text-xs font-bold leading-5 ${getMessageClass(message.tone)}`}>
          <div className="mb-1 flex items-center gap-2 font-black">
            {message.tone === "success" ? (
              <CheckCircle2 size={16} />
            ) : message.tone === "warning" ? (
              <ShieldAlert size={16} />
            ) : (
              <AlertCircle size={16} />
            )}
            {texts.resultTitle}
          </div>
          {message.text}
        </div>
      )}

      <div className="space-y-2.5">
        <label className="block">
          <span className="mb-1.5 block text-xs font-black text-slate-700 dark:text-slate-200">
            {texts.staffLabel}
          </span>

          <select
            value={selectedUserId}
            onChange={(event) => {
              const value = event.target.value

              if (value === "all" || value === "") {
                setSelectedUserId(value)
              } else {
                setSelectedUserId(Number(value))
              }
            }}
            className="min-h-12 w-full rounded-2xl border border-white/80 bg-white px-3 text-sm font-bold text-slate-900 outline-none focus:border-cyan-400 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
          >
            <option value="">{texts.staffSelectPlaceholder}</option>
            {targetUsers.length > 1 && <option value="all">{texts.allEligibleStaff}</option>}
            {targetUsers.map((user) => (
              <option key={user.id} value={user.id}>
                {getUserLabel(user)}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="mb-1.5 block text-xs font-black text-slate-700 dark:text-slate-200">
            {texts.noteLabel}
          </span>

          <textarea
            value={requestNote}
            onChange={(event) => setRequestNote(event.target.value)}
            rows={2}
            maxLength={1000}
            placeholder={texts.notePlaceholder}
            className="w-full resize-none rounded-2xl border border-white/80 bg-white px-3 py-2 text-sm font-bold text-slate-900 outline-none focus:border-cyan-400 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
          />
        </label>

        <button
          type="button"
          onClick={() => void handleRequestLocation()}
          disabled={isSending || isLoading || targetUsers.length === 0}
          className="flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-cyan-600 px-4 text-sm font-black text-white shadow-lg shadow-cyan-500/20 transition active:scale-95 disabled:cursor-wait disabled:opacity-60"
        >
          {isSending ? (
            <>
              <Loader2 className="animate-spin" size={18} />
              {texts.sending}
            </>
          ) : (
            <>
              <Send size={18} />
              {texts.sendButton}
            </>
          )}
        </button>
      </div>

      <div className="mt-4 border-t border-cyan-200 pt-3 dark:border-cyan-900">
        <div className="mb-2 flex items-center justify-between gap-3">
          <p className="text-xs font-black uppercase tracking-[0.14em] text-cyan-700 dark:text-cyan-200">
            {texts.recentTitle}
          </p>

          <div className="inline-flex items-center gap-1.5 rounded-full bg-white/70 px-2.5 py-1 text-[0.65rem] font-black text-cyan-700 dark:bg-slate-900 dark:text-cyan-100">
            <UsersRound size={13} />
            {checks.length}
          </div>
        </div>

        {recentChecks.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-cyan-200 bg-white/60 p-4 text-center text-xs font-bold leading-5 text-slate-600 dark:border-cyan-900 dark:bg-slate-950/50 dark:text-slate-300">
            {texts.emptyRecent}
          </div>
        ) : (
          <div className="space-y-2">
            {recentChecks.map((check) => (
              <article
                key={check.id}
                className="rounded-2xl border border-white/80 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-950/70"
              >
                <div className="mb-2 flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-black text-slate-950 dark:text-white">
                      {check.target_user_full_name || check.target_username || `${texts.userFallbackPrefix} #${check.target_user_id}`}
                    </p>
                    <p className="mt-0.5 text-xs font-bold text-slate-500 dark:text-slate-400">
                      {formatDateTime(check.requested_at_utc, language)}
                    </p>
                  </div>

                  <span className={`rounded-full px-2.5 py-1 text-[0.65rem] font-black ${getStatusClass(check)}`}>
                    {getStatusLabel(check, texts)}
                  </span>
                </div>

                <div className="flex flex-wrap gap-1.5 text-[0.68rem] font-bold text-slate-500 dark:text-slate-400">
                  <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1 dark:bg-slate-900">
                    <BellRing size={12} />
                    {getNotificationLabel(check, texts)}
                  </span>

                  {check.responded_at_utc && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1 dark:bg-slate-900">
                      <Clock3 size={12} />
                      {texts.responsePrefix}: {formatDateTime(check.responded_at_utc, language)}
                    </span>
                  )}

                  {check.location_accuracy !== null && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1 dark:bg-slate-900">
                      <MapPin size={12} />
                      ?{Math.round(check.location_accuracy)} m
                    </span>
                  )}
                </div>

                {buildGoogleMapsUrl(check) && (
                  <div className="mt-3 rounded-2xl border border-cyan-100 bg-cyan-50/70 p-3 dark:border-cyan-900 dark:bg-cyan-950/20">
                    <div className="mb-2 grid grid-cols-2 gap-2 text-[0.68rem] font-bold text-slate-600 dark:text-slate-300">
                      <div>
                        <span className="block text-slate-400 dark:text-slate-500">{texts.latitude}</span>
                        <span className="font-black">{formatCoordinate(check.latitude)}</span>
                      </div>

                      <div>
                        <span className="block text-slate-400 dark:text-slate-500">{texts.longitude}</span>
                        <span className="font-black">{formatCoordinate(check.longitude)}</span>
                      </div>
                    </div>

                    <a
                      href={buildGoogleMapsUrl(check) || "#"}
                      target="_blank"
                      rel="noreferrer"
                      className="flex min-h-10 w-full items-center justify-center gap-2 rounded-2xl bg-cyan-600 px-3 text-xs font-black text-white shadow-sm transition active:scale-95"
                    >
                      <MapPin size={15} />
                      {texts.openMap}
                    </a>
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
