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
}

type ActionMessage = {
  tone: "success" | "error" | "warning"
  text: string
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "-"
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return "-"
  }

  return date.toLocaleString("tr-TR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function getRequestSourceLabel(check: LocationCheck) {
  if (check.requested_by_user_full_name) {
    return check.requested_by_user_full_name
  }

  return "Yetkili kullanıcı"
}

function getNotificationLabel(check: LocationCheck) {
  if (check.notification_status === "sent") {
    return "Bildirim gönderildi"
  }

  if (check.notification_status === "partial_failed") {
    return "Bildirim kısmen gönderildi"
  }

  if (check.notification_status === "no_subscription") {
    return "Cihaz bildirime kayıtlı değil"
  }

  if (check.notification_status === "failed") {
    return "Bildirim gönderilemedi"
  }

  if (check.notification_status === "configuration_error") {
    return "Bildirim ayarı eksik"
  }

  return "Bildirim beklemede"
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

export function StaffLocationCheckPanel({ onChanged }: StaffLocationCheckPanelProps) {
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
      } catch (error) {
        if (error instanceof Error) {
          setErrorMessage(error.message)
        } else {
          setErrorMessage("Konum yoklama istekleri alınamadı.")
        }
      } finally {
        setIsLoading(false)
        setIsRefreshing(false)
      }
    },
    [],
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
        text: "Konumun başarıyla paylaşıldı.",
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
        text: responseErrorMessage,
      })

      await loadPendingChecks(false)
      onChanged?.()
    } finally {
      setBusyCheckId(null)
    }
  }

  if (isLoading) {
    return (
      <section className="rounded-[1.75rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
            <Loader2 className="animate-spin" size={21} />
          </div>

          <div>
            <p className="text-sm font-black">Konum yoklaması kontrol ediliyor</p>
            <p className="mt-1 text-xs font-semibold text-[var(--missio-text-muted)]">
              Bekleyen konum istekleri hazırlanıyor.
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
              Konum yoklaması
            </p>
            <h2 className="mt-1 text-base font-black text-slate-950 dark:text-white">
              Bekleyen konum isteği
            </h2>
            <p className="mt-1 text-xs font-bold leading-5 text-slate-700 dark:text-slate-200">
              Yetkili kişi konumunu paylaşmanı istiyor.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => void loadPendingChecks(false)}
          disabled={isRefreshing}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-white/80 text-cyan-700 shadow-sm transition active:scale-95 disabled:cursor-wait disabled:opacity-60 dark:bg-slate-900 dark:text-cyan-100"
          aria-label="Konum yoklamalarını yenile"
        >
          {isRefreshing ? <Loader2 className="animate-spin" size={18} /> : <RefreshCw size={18} />}
        </button>
      </div>

      {errorMessage && (
        <div className="mb-3 rounded-2xl border border-red-200 bg-red-50 p-3 text-xs font-bold leading-5 text-red-800 dark:border-red-900 dark:bg-red-950/30 dark:text-red-100">
          <div className="mb-1 flex items-center gap-2 font-black">
            <AlertCircle size={16} />
            Konum istekleri alınamadı
          </div>
          {errorMessage}
        </div>
      )}

      {actionMessage && (
        <div className={`mb-3 rounded-2xl border p-3 text-xs font-bold leading-5 ${getActionMessageClass(actionMessage.tone)}`}>
          <div className="mb-1 flex items-center gap-2 font-black">
            {actionMessage.tone === "success" ? <CheckCircle2 size={16} /> : <ShieldAlert size={16} />}
            İşlem sonucu
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
                    {getRequestSourceLabel(check)}
                  </p>
                  <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
                    İstek zamanı: {formatDateTime(check.requested_at_utc)}
                  </p>
                </div>

                <span className="rounded-full bg-cyan-100 px-2.5 py-1 text-[0.65rem] font-black text-cyan-700 dark:bg-cyan-950 dark:text-cyan-100">
                  {check.status === "seen" ? "Görüldü" : "Bekliyor"}
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
                  {getNotificationLabel(check)}
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
                    Konum alınıyor
                  </>
                ) : (
                  <>
                    <MapPin size={18} />
                    Konumumu Paylaş
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
