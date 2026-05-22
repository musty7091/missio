import { useEffect, useState } from "react"
import {
  FileText,
  RefreshCw,
  X,
} from "lucide-react"

import {
  getDailyOperationClosure,
  listDailyOperationClosures,
  type DailyOperationClosure,
} from "../../services/dailyClosureService"

type BossReportsPanelProps = {
  businessId: number | null
}

function formatDate(value: string | null) {
  if (!value) {
    return "Tarih yok"
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleDateString("tr-TR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  })
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "Tarih yok"
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return "Tarih yok"
  }

  return date.toLocaleString("tr-TR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function getClosureStatusLabel(status: string) {
  if (status === "closed_clean") {
    return "Temiz kapanış"
  }

  if (status === "closed_with_issues") {
    return "Sorunlu kapanış"
  }

  if (status === "closed") {
    return "Gün kapatıldı"
  }

  return "Kapanış"
}

function getClosureIssueCount(closure: DailyOperationClosure) {
  const missingPhotoCount = Math.max(
    closure.photo_required_task_count - closure.photo_evidence_task_count,
    0,
  )

  return (
    closure.open_task_count +
    closure.rejected_task_count +
    closure.approval_pending_task_count +
    missingPhotoCount
  )
}

function getClosureStatusClassName(status: string) {
  if (status === "closed_with_issues") {
    return "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200"
  }

  return "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200"
}

function getTaskStatusLabel(status: string, requiresManagerApproval: boolean) {
  if (status === "assigned") {
    return "Bekliyor"
  }

  if (status === "in_progress") {
    return "Devam ediyor"
  }

  if (status === "rejected") {
    return "Reddedildi"
  }

  if (status === "completed" && requiresManagerApproval) {
    return "Onay bekliyor"
  }

  if (status === "completed") {
    return "Tamamlandı"
  }

  if (status === "approved") {
    return "Onaylandı"
  }

  if (status === "cancelled") {
    return "İptal"
  }

  return "Durum"
}

function isProblemItem(item: DailyOperationClosure["items"][number]) {
  if (
    item.task_status === "assigned" ||
    item.task_status === "in_progress" ||
    item.task_status === "rejected"
  ) {
    return true
  }

  if (item.task_status === "completed" && item.requires_manager_approval) {
    return true
  }

  if (item.requires_photo && !item.has_photo_evidence) {
    return true
  }

  return false
}

function ReportsDetailModal({
  closure,
  isLoading,
  onClose,
}: {
  closure: DailyOperationClosure
  isLoading: boolean
  onClose: () => void
}) {
  const issueCount = getClosureIssueCount(closure)
  const problemItems = closure.items.filter(isProblemItem)

  useEffect(() => {
    const scrollY = window.scrollY
    const originalOverflow = document.body.style.overflow
    const originalPosition = document.body.style.position
    const originalTop = document.body.style.top
    const originalLeft = document.body.style.left
    const originalRight = document.body.style.right
    const originalWidth = document.body.style.width

    document.body.style.overflow = "hidden"
    document.body.style.position = "fixed"
    document.body.style.top = `-${scrollY}px`
    document.body.style.left = "0"
    document.body.style.right = "0"
    document.body.style.width = "100%"

    return () => {
      document.body.style.overflow = originalOverflow
      document.body.style.position = originalPosition
      document.body.style.top = originalTop
      document.body.style.left = originalLeft
      document.body.style.right = originalRight
      document.body.style.width = originalWidth
      window.scrollTo(0, scrollY)
    }
  }, [])

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center overflow-hidden overscroll-none bg-slate-950/55 px-3 pb-[max(1rem,env(safe-area-inset-bottom))] pt-[max(7.5rem,env(safe-area-inset-top))] backdrop-blur-sm">
      <div className="max-h-[calc(100dvh-9rem)] w-full max-w-[430px] overflow-y-auto overscroll-contain rounded-[2rem] bg-[var(--missio-page-bg)] p-4 shadow-2xl">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
              Gün sonu raporu
            </p>

            <h2 className="mt-1 text-xl font-black text-[var(--missio-text-main)]">
              {formatDate(closure.closure_date)}
            </h2>

            <p className="mt-1 text-sm font-bold text-[var(--missio-text-muted)]">
              Kapatan: {closure.closed_by_user_full_name}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[var(--missio-card-bg)] text-[var(--missio-text-main)] shadow-sm"
            aria-label="Kapat"
          >
            <X size={20} />
          </button>
        </div>

        {isLoading && (
          <div className="mb-3 rounded-2xl border border-cyan-200 bg-cyan-50 p-3 text-sm font-black text-cyan-800 dark:border-cyan-900 dark:bg-cyan-950 dark:text-cyan-200">
            Rapor detayı yükleniyor...
          </div>
        )}

        <section
          className={
            closure.status === "closed_with_issues"
              ? "mb-3 rounded-[1.5rem] border border-amber-200 bg-amber-50 p-3 dark:border-amber-900 dark:bg-amber-950/30"
              : "mb-3 rounded-[1.5rem] border border-emerald-200 bg-emerald-50 p-3 dark:border-emerald-900 dark:bg-emerald-950/30"
          }
        >
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-black text-[var(--missio-text-main)]">
                {getClosureStatusLabel(closure.status)}
              </p>

              <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
                Saat: {formatDateTime(closure.closed_at_utc)}
              </p>
            </div>

            <div className="rounded-2xl bg-white/70 px-3 py-2 text-center dark:bg-white/10">
              <p className="text-lg font-black text-[var(--missio-text-main)]">
                {issueCount}
              </p>
              <p className="text-[0.62rem] font-bold text-[var(--missio-text-muted)]">
                sorun
              </p>
            </div>
          </div>

          {closure.manager_note && (
            <div className="mt-3 rounded-2xl bg-white/70 p-3 text-sm font-bold leading-6 text-[var(--missio-text-main)] dark:bg-white/10">
              {closure.manager_note}
            </div>
          )}
        </section>

        <section className="mb-3 grid grid-cols-2 gap-2">
          <div className="rounded-2xl bg-[var(--missio-card-bg)] p-3 shadow-sm">
            <p className="text-2xl font-black text-[var(--missio-text-main)]">
              {closure.total_task_count}
            </p>
            <p className="text-xs font-bold text-[var(--missio-text-muted)]">
              Toplam görev
            </p>
          </div>

          <div className="rounded-2xl bg-[var(--missio-card-bg)] p-3 shadow-sm">
            <p className="text-2xl font-black text-emerald-600">
              {closure.completed_task_count}
            </p>
            <p className="text-xs font-bold text-[var(--missio-text-muted)]">
              Tamamlanan
            </p>
          </div>

          <div className="rounded-2xl bg-[var(--missio-card-bg)] p-3 shadow-sm">
            <p className="text-2xl font-black text-amber-600">
              {closure.approval_pending_task_count}
            </p>
            <p className="text-xs font-bold text-[var(--missio-text-muted)]">
              Onay bekleyen
            </p>
          </div>

          <div className="rounded-2xl bg-[var(--missio-card-bg)] p-3 shadow-sm">
            <p className="text-2xl font-black text-rose-600">
              {closure.rejected_task_count}
            </p>
            <p className="text-xs font-bold text-[var(--missio-text-muted)]">
              Reddedilen
            </p>
          </div>
        </section>

        <section className="mb-3 rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                Sorunlu işler
              </p>
              <h3 className="mt-1 text-base font-black text-[var(--missio-text-main)]">
                Kontrol gerektiren görevler
              </h3>
            </div>

            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-black text-amber-800 dark:bg-amber-950 dark:text-amber-200">
              {problemItems.length}
            </span>
          </div>

          {problemItems.length === 0 ? (
            <div className="rounded-2xl bg-emerald-50 p-3 text-sm font-bold text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-200">
              Sorunlu görev görünmüyor.
            </div>
          ) : (
            <div className="space-y-2">
              {problemItems.map((item) => (
                <div
                  key={item.id}
                  className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-3"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-black text-[var(--missio-text-main)]">
                        {item.task_title}
                      </p>

                      <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
                        {item.assigned_to_user_full_name ||
                          item.assigned_to_username ||
                          "Personel yok"}
                      </p>
                    </div>

                    <span className="rounded-full bg-amber-100 px-2.5 py-1 text-[0.65rem] font-black text-amber-800 dark:bg-amber-950 dark:text-amber-200">
                      {getTaskStatusLabel(
                        item.task_status,
                        item.requires_manager_approval,
                      )}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
          <div className="mb-3">
            <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
              Görevler
            </p>
            <h3 className="mt-1 text-base font-black text-[var(--missio-text-main)]">
              Günün görev listesi
            </h3>
          </div>

          {closure.items.length === 0 ? (
            <div className="rounded-2xl bg-[var(--missio-page-bg)] p-3 text-sm font-bold text-[var(--missio-text-muted)]">
              Görev detayı bulunamadı.
            </div>
          ) : (
            <div className="space-y-2">
              {closure.items.map((item) => (
                <div
                  key={item.id}
                  className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-3"
                >
                  <div className="mb-2 flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-black text-[var(--missio-text-main)]">
                        {item.task_title}
                      </p>

                      <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
                        {item.assigned_to_user_full_name ||
                          item.assigned_to_username ||
                          "Personel yok"}
                      </p>
                    </div>

                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[0.65rem] font-black text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                      {getTaskStatusLabel(
                        item.task_status,
                        item.requires_manager_approval,
                      )}
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-1.5 text-[0.62rem] font-black">
                    {item.requires_photo && (
                      <span className="rounded-full bg-cyan-100 px-2 py-1 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200">
                        Fotoğraf {item.has_photo_evidence ? "var" : "yok"}
                      </span>
                    )}

                    {item.requires_manager_approval && (
                      <span className="rounded-full bg-violet-100 px-2 py-1 text-violet-700 dark:bg-violet-950 dark:text-violet-200">
                        Onaylı iş
                      </span>
                    )}

                    <span className="rounded-full bg-slate-100 px-2 py-1 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                      {item.task_type === "routine" ? "Rutin" : "Ekstra"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

export function BossReportsPanel({ businessId }: BossReportsPanelProps) {
  const [closures, setClosures] = useState<DailyOperationClosure[]>([])
  const [selectedClosure, setSelectedClosure] =
    useState<DailyOperationClosure | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isDetailLoading, setIsDetailLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  async function loadReports() {
    if (!businessId) {
      setClosures([])
      setErrorMessage("Bu kullanıcı için işletme bilgisi bulunamadı.")
      return
    }

    setIsLoading(true)
    setErrorMessage(null)

    try {
      const response = await listDailyOperationClosures({
        businessId,
        limit: 60,
        offset: 0,
      })

      setClosures(response.closures)
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Gün sonu raporları yüklenemedi.")
      }
    } finally {
      setIsLoading(false)
    }
  }

  async function openDetail(closure: DailyOperationClosure) {
    setSelectedClosure(closure)
    setIsDetailLoading(true)
    setErrorMessage(null)

    try {
      const detail = await getDailyOperationClosure(closure.id)
      setSelectedClosure(detail)
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Rapor detayı yüklenemedi.")
      }
    } finally {
      setIsDetailLoading(false)
    }
  }

  useEffect(() => {
    void loadReports()
  }, [businessId])

  const cleanCount = closures.filter(
    (closure) => closure.status === "closed_clean" || closure.status === "closed",
  ).length
  const issueCount = closures.filter(
    (closure) => closure.status === "closed_with_issues",
  ).length

  return (
    <div className="space-y-4">
      <section className="rounded-[2rem] bg-gradient-to-br from-slate-950 via-slate-900 to-cyan-950 p-4 text-white shadow-xl shadow-slate-950/20">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-black text-cyan-100">
              <FileText size={14} />
              Rapor arşivi
            </div>

            <h1 className="text-2xl font-black tracking-tight">
              Gün sonu raporları
            </h1>

            <p className="mt-2 max-w-sm text-sm font-bold leading-6 text-slate-300">
              Kapanan günlerin resmi operasyon kayıtları. Raporlar son 60 gün saklanır.
            </p>
          </div>

          <button
            type="button"
            onClick={() => void loadReports()}
            disabled={isLoading}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/10 text-cyan-100 transition active:scale-95 disabled:opacity-60"
            aria-label="Yenile"
          >
            <RefreshCw className={isLoading ? "animate-spin" : ""} size={19} />
          </button>
        </div>

        <div className="grid grid-cols-3 gap-2">
          <div className="rounded-2xl bg-white/10 px-3 py-3">
            <p className="text-2xl font-black">{closures.length}</p>
            <p className="mt-1 text-[0.68rem] font-bold text-slate-300">
              Rapor
            </p>
          </div>

          <div className="rounded-2xl bg-white/10 px-3 py-3">
            <p className="text-2xl font-black">{cleanCount}</p>
            <p className="mt-1 text-[0.68rem] font-bold text-slate-300">
              Temiz
            </p>
          </div>

          <div className="rounded-2xl bg-white/10 px-3 py-3">
            <p className="text-2xl font-black">{issueCount}</p>
            <p className="mt-1 text-[0.68rem] font-bold text-slate-300">
              Sorunlu
            </p>
          </div>
        </div>
      </section>

      {errorMessage && (
        <div className="rounded-[1.35rem] border border-rose-200 bg-rose-50 p-3 text-sm font-black text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
          {errorMessage}
        </div>
      )}

      <section className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
              Arşiv
            </p>

            <h2 className="mt-1 text-base font-black text-[var(--missio-text-main)]">
              Son 60 gün
            </h2>
          </div>

          <span className="rounded-full bg-cyan-100 px-3 py-1 text-xs font-black text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200">
            {closures.length}
          </span>
        </div>

        {isLoading ? (
          <div className="rounded-2xl bg-[var(--missio-page-bg)] p-4 text-sm font-bold leading-6 text-[var(--missio-text-muted)]">
            Raporlar yükleniyor...
          </div>
        ) : closures.length === 0 ? (
          <div className="rounded-2xl bg-[var(--missio-page-bg)] p-4 text-sm font-bold leading-6 text-[var(--missio-text-muted)]">
            Henüz gün sonu raporu oluşturulmamış.
          </div>
        ) : (
          <div className="space-y-2">
            {closures.map((closure) => {
              const closureIssueCount = getClosureIssueCount(closure)

              return (
                <div
                  key={closure.id}
                  className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-3"
                >
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <div>
                      <p className="text-base font-black text-[var(--missio-text-main)]">
                        {formatDate(closure.closure_date)}
                      </p>

                      <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
                        Kapatan: {closure.closed_by_user_full_name}
                      </p>
                    </div>

                    <span
                      className={`rounded-full px-2.5 py-1 text-[0.65rem] font-black ${getClosureStatusClassName(
                        closure.status,
                      )}`}
                    >
                      {getClosureStatusLabel(closure.status)}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-xl bg-white/60 px-2 py-2 dark:bg-white/5">
                      <p className="text-base font-black text-[var(--missio-text-main)]">
                        {closure.total_task_count}
                      </p>
                      <p className="text-[0.62rem] font-bold text-[var(--missio-text-muted)]">
                        Toplam
                      </p>
                    </div>

                    <div className="rounded-xl bg-white/60 px-2 py-2 dark:bg-white/5">
                      <p className="text-base font-black text-emerald-600">
                        {closure.completed_task_count}
                      </p>
                      <p className="text-[0.62rem] font-bold text-[var(--missio-text-muted)]">
                        Tamam
                      </p>
                    </div>

                    <div className="rounded-xl bg-white/60 px-2 py-2 dark:bg-white/5">
                      <p
                        className={
                          closureIssueCount > 0
                            ? "text-base font-black text-amber-600"
                            : "text-base font-black text-emerald-600"
                        }
                      >
                        {closureIssueCount}
                      </p>
                      <p className="text-[0.62rem] font-bold text-[var(--missio-text-muted)]">
                        Sorun
                      </p>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => void openDetail(closure)}
                    className="mt-3 flex min-h-11 w-full items-center justify-center rounded-2xl bg-cyan-500 px-4 py-2 text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/20 transition active:scale-95"
                  >
                    Detayı Gör
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </section>

      {selectedClosure && (
        <ReportsDetailModal
          closure={selectedClosure}
          isLoading={isDetailLoading}
          onClose={() => setSelectedClosure(null)}
        />
      )}
    </div>
  )
}
