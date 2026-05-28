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

function getStatusLabel(check: LocationCheck) {
  if (check.status === "pending") return "Bekleniyor"
  if (check.status === "seen") return "Görüldü"
  if (check.status === "shared") return "Konum paylaşıldı"
  if (check.status === "permission_denied") return "Konum izni kapalı"
  if (check.status === "failed") return "Başarısız"
  if (check.status === "expired") return "Süre doldu"
  if (check.status === "cancelled") return "İptal"

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
    return "Bildirim başarısız"
  }

  if (check.notification_status === "configuration_error") {
    return "Bildirim ayarı eksik"
  }

  return "Bildirim beklemede"
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

export function LocationCheckRequestPanel({
  businessId,
  allowedTargetRoles = ["manager", "staff"],
}: LocationCheckRequestPanelProps) {
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
      } catch (error) {
        setMessage({
          tone: "error",
          text:
            error instanceof Error
              ? error.message
              : "Konum yoklama bilgileri alınamadı.",
        })
      } finally {
        setIsLoading(false)
      }
    },
    [businessId],
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
        text: "İşletme bilgisi bulunamadı.",
      })
      return
    }

    if (!selectedUserId) {
      setMessage({
        tone: "warning",
        text: "Konum istemek için personel seçmelisin.",
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
        text: "Konum istenebilecek aktif personel bulunamadı.",
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
            ? `${response.created_count} konum isteği oluşturuldu. ${noSubscriptionCount} kişide bildirim kaydı yok; istek yine de uygulama içinde bekleyecek.`
            : `${response.created_count} konum isteği oluşturuldu.`,
      })

      setRequestNote("")
      setSelectedUserId("")
      await loadPanelData(false)
    } catch (error) {
      setMessage({
        tone: "error",
        text:
          error instanceof Error
            ? error.message
            : "Konum isteği oluşturulamadı.",
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
              Konum yoklama
            </p>
            <h2 className="mt-1 text-base font-black text-slate-950 dark:text-white">
              Personelden konum iste
            </h2>
            <p className="mt-1 text-xs font-bold leading-5 text-slate-700 dark:text-slate-200">
              Personel uygulamayı açtığında bekleyen konum isteğini görür.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => void loadPanelData(false)}
          disabled={isLoading}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-white/80 text-cyan-700 shadow-sm transition active:scale-95 disabled:cursor-wait disabled:opacity-60 dark:bg-slate-900 dark:text-cyan-100"
          aria-label="Konum yoklama panelini yenile"
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
            İşlem sonucu
          </div>
          {message.text}
        </div>
      )}

      <div className="space-y-2.5">
        <label className="block">
          <span className="mb-1.5 block text-xs font-black text-slate-700 dark:text-slate-200">
            Personel
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
            <option value="">Personel seç</option>
            {targetUsers.length > 1 && <option value="all">Tüm uygun personeller</option>}
            {targetUsers.map((user) => (
              <option key={user.id} value={user.id}>
                {getUserLabel(user)}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="mb-1.5 block text-xs font-black text-slate-700 dark:text-slate-200">
            Not
          </span>

          <textarea
            value={requestNote}
            onChange={(event) => setRequestNote(event.target.value)}
            rows={2}
            maxLength={1000}
            placeholder="Örn: Depo çıkışı öncesi konum paylaş."
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
              İstek gönderiliyor
            </>
          ) : (
            <>
              <Send size={18} />
              Konum İste
            </>
          )}
        </button>
      </div>

      <div className="mt-4 border-t border-cyan-200 pt-3 dark:border-cyan-900">
        <div className="mb-2 flex items-center justify-between gap-3">
          <p className="text-xs font-black uppercase tracking-[0.14em] text-cyan-700 dark:text-cyan-200">
            Son yoklamalar
          </p>

          <div className="inline-flex items-center gap-1.5 rounded-full bg-white/70 px-2.5 py-1 text-[0.65rem] font-black text-cyan-700 dark:bg-slate-900 dark:text-cyan-100">
            <UsersRound size={13} />
            {checks.length}
          </div>
        </div>

        {recentChecks.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-cyan-200 bg-white/60 p-4 text-center text-xs font-bold leading-5 text-slate-600 dark:border-cyan-900 dark:bg-slate-950/50 dark:text-slate-300">
            Henüz konum yoklaması oluşturulmadı.
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
                      {check.target_user_full_name || check.target_username || `Kullanıcı #${check.target_user_id}`}
                    </p>
                    <p className="mt-0.5 text-xs font-bold text-slate-500 dark:text-slate-400">
                      {formatDateTime(check.requested_at_utc)}
                    </p>
                  </div>

                  <span className={`rounded-full px-2.5 py-1 text-[0.65rem] font-black ${getStatusClass(check)}`}>
                    {getStatusLabel(check)}
                  </span>
                </div>

                <div className="flex flex-wrap gap-1.5 text-[0.68rem] font-bold text-slate-500 dark:text-slate-400">
                  <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1 dark:bg-slate-900">
                    <BellRing size={12} />
                    {getNotificationLabel(check)}
                  </span>

                  {check.responded_at_utc && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1 dark:bg-slate-900">
                      <Clock3 size={12} />
                      Yanıt: {formatDateTime(check.responded_at_utc)}
                    </span>
                  )}

                  {check.location_accuracy !== null && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1 dark:bg-slate-900">
                      <MapPin size={12} />
                      ±{Math.round(check.location_accuracy)} m
                    </span>
                  )}
                </div>

                {buildGoogleMapsUrl(check) && (
                  <div className="mt-3 rounded-2xl border border-cyan-100 bg-cyan-50/70 p-3 dark:border-cyan-900 dark:bg-cyan-950/20">
                    <div className="mb-2 grid grid-cols-2 gap-2 text-[0.68rem] font-bold text-slate-600 dark:text-slate-300">
                      <div>
                        <span className="block text-slate-400 dark:text-slate-500">Enlem</span>
                        <span className="font-black">{formatCoordinate(check.latitude)}</span>
                      </div>

                      <div>
                        <span className="block text-slate-400 dark:text-slate-500">Boylam</span>
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
                      Haritada Aç
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
