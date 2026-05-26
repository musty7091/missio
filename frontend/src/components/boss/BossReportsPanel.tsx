import { useEffect, useState } from "react"
import { useTranslation, type TranslationKey } from "../../i18n/language"
import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  Download,
  Eye,
  FileText,
  RefreshCw,
  X,
} from "lucide-react"

import {
  downloadDailyOperationClosurePdf,
  getDailyOperationClosure,
  listDailyOperationClosures,
  type DailyOperationClosure,
} from "../../services/dailyClosureService"

type BossReportsPanelProps = {
  businessId: number | null
}

type ClosureItem = DailyOperationClosure["items"][number]

function formatDate(
  value: string | null,
  language: "tr" | "en",
  t: (key: TranslationKey) => string,
) {
  if (!value) {
    return t("boss.report.date.none")
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleDateString(language === "tr" ? "tr-TR" : "en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  })
}

function formatDateTime(
  value: string | null,
  language: "tr" | "en",
  t: (key: TranslationKey) => string,
) {
  if (!value) {
    return t("boss.report.date.none")
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return t("boss.report.date.none")
  }

  return date.toLocaleString(language === "tr" ? "tr-TR" : "en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function getClosureStatusLabel(
  status: string,
  t: (key: TranslationKey) => string,
) {
  if (status === "closed_clean" || status === "closed") {
    return t("boss.report.status.clean")
  }

  if (status === "closed_with_issues") {
    return t("boss.report.status.withIssues")
  }

  return t("boss.report.status.default")
}

function getClosureStatusClassName(status: string) {
  if (status === "closed_with_issues") {
    return "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200"
  }

  return "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200"
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

function getTaskStatusLabel(
  status: string,
  requiresManagerApproval: boolean,
  t: (key: TranslationKey) => string,
) {
  if (status === "assigned") {
    return t("boss.report.task.status.assigned")
  }

  if (status === "in_progress") {
    return t("boss.report.task.status.inProgress")
  }

  if (status === "rejected") {
    return t("boss.report.task.status.rejected")
  }

  if (status === "completed" && requiresManagerApproval) {
    return t("boss.report.task.status.approvalPending")
  }

  if (status === "completed") {
    return t("boss.report.task.status.completed")
  }

  if (status === "approved") {
    return t("boss.report.task.status.approved")
  }

  if (status === "cancelled") {
    return t("boss.report.task.status.cancelled")
  }

  return t("boss.report.task.status.none")
}

function getTaskStatusClassName(status: string, requiresManagerApproval: boolean) {
  if (status === "rejected") {
    return "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-200"
  }

  if (status === "assigned" || status === "in_progress") {
    return "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-200"
  }

  if (status === "completed" && requiresManagerApproval) {
    return "bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-200"
  }

  if (status === "completed" || status === "approved") {
    return "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200"
  }

  return "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200"
}

function isProblemItem(item: ClosureItem) {
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

function getAssignedPersonLabel(
  item: ClosureItem,
  t: (key: TranslationKey) => string,
) {
  return (
    item.assigned_to_user_full_name ||
    item.assigned_to_username ||
    t("boss.report.task.noStaff")
  )
}

function PdfDownloadButton({
  closureId,
  compact = false,
  isDownloading,
  onDownload,
}: {
  closureId: number
  compact?: boolean
  isDownloading: boolean
  onDownload: (closureId: number) => void
}) {
  const { t } = useTranslation()

  return (
    <button
      type="button"
      onClick={() => onDownload(closureId)}
      disabled={isDownloading}
      className={
        compact
          ? "flex min-h-10 items-center justify-center gap-2 rounded-2xl border border-cyan-200 bg-cyan-50 px-3 py-2 text-xs font-black text-cyan-800 shadow-sm transition active:scale-95 disabled:cursor-wait disabled:opacity-60 dark:border-cyan-900 dark:bg-cyan-950/40 dark:text-cyan-200"
          : "flex min-h-11 w-full items-center justify-center gap-2 rounded-2xl bg-cyan-500 px-4 py-2 text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/20 transition active:scale-95 disabled:cursor-wait disabled:opacity-60"
      }
    >
      {isDownloading ? (
        <RefreshCw className="animate-spin" size={compact ? 15 : 17} />
      ) : (
        <Download size={compact ? 15 : 17} />
      )}
      {isDownloading ? t("boss.report.pdf.preparing") : t("boss.report.pdf.download")}
    </button>
  )
}

function ReportMetricCard({
  label,
  value,
  tone = "default",
}: {
  label: string
  value: number
  tone?: "default" | "success" | "warning" | "danger"
}) {
  const valueClassName = {
    default: "text-[var(--missio-text-main)]",
    success: "text-emerald-600",
    warning: "text-amber-600",
    danger: "text-rose-600",
  }[tone]

  return (
    <div className="rounded-2xl bg-[var(--missio-card-bg)] p-3 shadow-sm">
      <p className={`text-2xl font-black ${valueClassName}`}>{value}</p>
      <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
        {label}
      </p>
    </div>
  )
}

function ReportTaskRow({ item }: { item: ClosureItem }) {
  const { t } = useTranslation()

  return (
    <div className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-3">
      <div className="mb-2 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-black text-[var(--missio-text-main)]">
            {item.task_title}
          </p>

          <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
            {getAssignedPersonLabel(item, t)}
          </p>
        </div>

        <span
          className={`shrink-0 rounded-full px-2.5 py-1 text-[0.65rem] font-black ${getTaskStatusClassName(
            item.task_status,
            item.requires_manager_approval,
          )}`}
        >
          {getTaskStatusLabel(item.task_status, item.requires_manager_approval, t)}
        </span>
      </div>

      <div className="flex flex-wrap gap-1.5 text-[0.62rem] font-black">
        <span className="rounded-full bg-slate-100 px-2 py-1 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
          {item.task_type === "routine" ? t("boss.report.task.routine") : t("boss.report.task.oneTime")}
        </span>

        {item.requires_photo && (
          <span
            className={
              item.has_photo_evidence
                ? "rounded-full bg-emerald-100 px-2 py-1 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200"
                : "rounded-full bg-rose-100 px-2 py-1 text-rose-700 dark:bg-rose-950 dark:text-rose-200"
            }
          >
            {item.has_photo_evidence ? t("boss.report.task.photoAvailable") : t("boss.report.task.photoMissing")}
          </span>
        )}

        {item.requires_location && (
          <span className="rounded-full bg-cyan-100 px-2 py-1 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200">
            {t("boss.report.task.locationRequired")}
          </span>
        )}

        {item.requires_manager_approval && (
          <span className="rounded-full bg-violet-100 px-2 py-1 text-violet-700 dark:bg-violet-950 dark:text-violet-200">
            {t("boss.report.task.approvalRequired")}
          </span>
        )}
      </div>
    </div>
  )
}

function ReportsDetailModal({
  closure,
  isLoading,
  isPdfDownloading,
  onClose,
  onDownloadPdf,
}: {
  closure: DailyOperationClosure
  isLoading: boolean
  isPdfDownloading: boolean
  onClose: () => void
  onDownloadPdf: (closureId: number) => void
}) {
  const { language, t } = useTranslation()
  const closureIssueCount = getClosureIssueCount(closure)
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
          <div className="min-w-0">
            <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
              {t("boss.report.modal.eyebrow")}
            </p>

            <h2 className="mt-1 text-xl font-black text-[var(--missio-text-main)]">
              {formatDate(closure.closure_date, language, t)}
            </h2>

            <p className="mt-1 text-sm font-bold text-[var(--missio-text-muted)]">
              {t("boss.report.closedBy")}: {closure.closed_by_user_full_name}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-card-bg)] text-[var(--missio-text-main)] shadow-sm transition active:scale-95"
            aria-label={t("boss.report.modal.close")}
          >
            <X size={20} />
          </button>
        </div>

        {isLoading && (
          <div className="mb-3 rounded-2xl border border-cyan-200 bg-cyan-50 p-3 text-sm font-black text-cyan-800 dark:border-cyan-900 dark:bg-cyan-950 dark:text-cyan-200">
            {t("boss.report.modal.loading")}
          </div>
        )}

        <section
          className={`mb-3 rounded-[1.5rem] border p-3 ${getClosureStatusClassName(
            closure.status,
          )}`}
        >
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                {closure.status === "closed_with_issues" ? (
                  <AlertTriangle size={18} />
                ) : (
                  <CheckCircle2 size={18} />
                )}

                <p className="text-sm font-black">
                  {getClosureStatusLabel(closure.status, t)}
                </p>
              </div>

              <p className="mt-1 text-xs font-bold opacity-80">
                {t("boss.report.modal.closingTime")}: {formatDateTime(closure.closed_at_utc, language, t)}
              </p>
            </div>

            <div className="rounded-2xl bg-white/70 px-3 py-2 text-center dark:bg-white/10">
              <p className="text-lg font-black">{closureIssueCount}</p>
              <p className="text-[0.62rem] font-bold opacity-80">{t("boss.report.modal.issueUnit")}</p>
            </div>
          </div>

          {closure.manager_note && (
            <div className="mt-3 rounded-2xl bg-white/70 p-3 text-sm font-bold leading-6 dark:bg-white/10">
              {closure.manager_note}
            </div>
          )}
        </section>

        <section className="mb-3 grid grid-cols-2 gap-2">
          <ReportMetricCard label={t("boss.report.modal.metrics.totalTask")} value={closure.total_task_count} />
          <ReportMetricCard
            label={t("boss.report.modal.metrics.completed")}
            value={closure.completed_task_count}
            tone="success"
          />
          <ReportMetricCard
            label={t("boss.report.modal.metrics.approvalPending")}
            value={closure.approval_pending_task_count}
            tone={closure.approval_pending_task_count > 0 ? "warning" : "success"}
          />
          <ReportMetricCard
            label={t("boss.report.modal.metrics.rejected")}
            value={closure.rejected_task_count}
            tone={closure.rejected_task_count > 0 ? "danger" : "success"}
          />
        </section>

        <section className="mb-3 rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                {t("boss.report.modal.reviewEyebrow")}
              </p>

              <h3 className="mt-1 text-base font-black text-[var(--missio-text-main)]">
                {t("boss.report.modal.problemTitle")}
              </h3>
            </div>

            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-black text-amber-800 dark:bg-amber-950 dark:text-amber-200">
              {problemItems.length}
            </span>
          </div>

          {problemItems.length === 0 ? (
            <div className="rounded-2xl bg-emerald-50 p-3 text-sm font-bold text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-200">
              {t("boss.report.modal.noProblem")}
            </div>
          ) : (
            <div className="space-y-2">
              {problemItems.map((item) => (
                <ReportTaskRow key={item.id} item={item} />
              ))}
            </div>
          )}
        </section>

        <section className="mb-3 rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
          <div className="mb-3">
            <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
              {t("boss.report.modal.snapshotEyebrow")}
            </p>

            <h3 className="mt-1 text-base font-black text-[var(--missio-text-main)]">
              {t("boss.report.modal.snapshotTitle")}
            </h3>
          </div>

          {closure.items.length === 0 ? (
            <div className="rounded-2xl bg-[var(--missio-page-bg)] p-3 text-sm font-bold text-[var(--missio-text-muted)]">
              {t("boss.report.modal.noTaskDetail")}
            </div>
          ) : (
            <div className="space-y-2">
              {closure.items.map((item) => (
                <ReportTaskRow key={item.id} item={item} />
              ))}
            </div>
          )}
        </section>

        <PdfDownloadButton
          closureId={closure.id}
          isDownloading={isPdfDownloading}
          onDownload={onDownloadPdf}
        />
      </div>
    </div>
  )
}

export function BossReportsPanel({ businessId }: BossReportsPanelProps) {
  const { language, t } = useTranslation()
  const [closures, setClosures] = useState<DailyOperationClosure[]>([])
  const [selectedClosure, setSelectedClosure] =
    useState<DailyOperationClosure | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isDetailLoading, setIsDetailLoading] = useState(false)
  const [downloadingPdfClosureId, setDownloadingPdfClosureId] = useState<number | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  async function loadReports() {
    if (!businessId) {
      setClosures([])
      setErrorMessage(t("boss.report.error.noBusiness"))
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
        setErrorMessage(t("boss.report.error.loadFailed"))
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
        setErrorMessage(t("boss.report.error.detailFailed"))
      }
    } finally {
      setIsDetailLoading(false)
    }
  }

  async function handleDownloadPdf(closureId: number) {
    setDownloadingPdfClosureId(closureId)
    setErrorMessage(null)

    try {
      const file = await downloadDailyOperationClosurePdf(closureId)
      const url = window.URL.createObjectURL(file.blob)
      const link = document.createElement("a")

      link.href = url
      link.download = file.filename
      document.body.appendChild(link)
      link.click()
      link.remove()

      window.URL.revokeObjectURL(url)
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage(t("boss.report.error.pdfFailed"))
      }
    } finally {
      setDownloadingPdfClosureId(null)
    }
  }

  useEffect(() => {
    void loadReports()
  }, [businessId])

  const cleanReportCount = closures.filter(
    (closure) => closure.status === "closed_clean" || closure.status === "closed",
  ).length

  const issueReportCount = closures.filter(
    (closure) => closure.status === "closed_with_issues",
  ).length

  return (
    <div className="space-y-4">
      <section className="rounded-[2rem] bg-gradient-to-br from-slate-950 via-slate-900 to-cyan-950 p-4 text-white shadow-xl shadow-slate-950/20">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-black text-cyan-100">
              <FileText size={14} />
              {t("boss.report.hero.badge")}
            </div>

            <h1 className="text-2xl font-black tracking-tight">
              {t("boss.report.hero.title")}
            </h1>

            <p className="mt-2 max-w-sm text-sm font-bold leading-6 text-slate-300">
              {t("boss.report.hero.description")}
            </p>
          </div>

          <button
            type="button"
            onClick={() => void loadReports()}
            disabled={isLoading}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/10 text-cyan-100 transition active:scale-95 disabled:opacity-60"
            aria-label={t("boss.report.refresh")}
          >
            <RefreshCw className={isLoading ? "animate-spin" : ""} size={19} />
          </button>
        </div>

        <div className="mt-4 grid grid-cols-3 gap-2">
          <div className="rounded-2xl bg-white/10 px-3 py-3">
            <p className="text-2xl font-black">{closures.length}</p>
            <p className="mt-1 text-[0.68rem] font-bold text-slate-300">
              {t("boss.report.stat.report")}
            </p>
          </div>

          <div className="rounded-2xl bg-white/10 px-3 py-3">
            <p className="text-2xl font-black">{cleanReportCount}</p>
            <p className="mt-1 text-[0.68rem] font-bold text-slate-300">
              {t("boss.report.stat.clean")}
            </p>
          </div>

          <div className="rounded-2xl bg-white/10 px-3 py-3">
            <p className="text-2xl font-black">{issueReportCount}</p>
            <p className="mt-1 text-[0.68rem] font-bold text-slate-300">
              {t("boss.report.stat.issue")}
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
              {t("boss.report.archive.eyebrow")}
            </p>

            <h2 className="mt-1 text-base font-black text-[var(--missio-text-main)]">
              {t("boss.report.archive.title")}
            </h2>
          </div>

          <span className="rounded-full bg-cyan-100 px-3 py-1 text-xs font-black text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200">
            {closures.length} {closures.length === 1 ? t("boss.report.archive.record") : t("boss.report.archive.records")}
          </span>
        </div>

        {isLoading ? (
          <div className="rounded-2xl bg-[var(--missio-page-bg)] p-4 text-sm font-bold leading-6 text-[var(--missio-text-muted)]">
            {t("boss.report.loading")}
          </div>
        ) : closures.length === 0 ? (
          <div className="rounded-2xl bg-[var(--missio-page-bg)] p-4 text-sm font-bold leading-6 text-[var(--missio-text-muted)]">
            {t("boss.report.empty")}
          </div>
        ) : (
          <div className="space-y-2">
            {closures.map((closure) => {
              const closureIssueCount = getClosureIssueCount(closure)

              return (
                <article
                  key={closure.id}
                  className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-3"
                >
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <CalendarDays
                          className="shrink-0 text-[var(--missio-text-muted)]"
                          size={16}
                        />

                        <p className="text-base font-black text-[var(--missio-text-main)]">
                          {formatDate(closure.closure_date, language, t)}
                        </p>
                      </div>

                      <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
                        {t("boss.report.closedBy")}: {closure.closed_by_user_full_name}
                      </p>

                      <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
                        {t("boss.report.time")}: {formatDateTime(closure.closed_at_utc, language, t)}
                      </p>
                    </div>

                    <span
                      className={`shrink-0 rounded-full border px-2.5 py-1 text-[0.65rem] font-black ${getClosureStatusClassName(
                        closure.status,
                      )}`}
                    >
                      {getClosureStatusLabel(closure.status, t)}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-xl bg-white/60 px-2 py-2 dark:bg-white/5">
                      <p className="text-base font-black text-[var(--missio-text-main)]">
                        {closure.total_task_count}
                      </p>
                      <p className="text-[0.62rem] font-bold text-[var(--missio-text-muted)]">
                        {t("boss.report.total")}
                      </p>
                    </div>

                    <div className="rounded-xl bg-white/60 px-2 py-2 dark:bg-white/5">
                      <p className="text-base font-black text-emerald-600">
                        {closure.completed_task_count}
                      </p>
                      <p className="text-[0.62rem] font-bold text-[var(--missio-text-muted)]">
                        {t("boss.report.done")}
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
                        {t("boss.report.issue")}
                      </p>
                    </div>
                  </div>

                  {closure.manager_note && (
                    <div className="mt-3 rounded-2xl bg-white/60 p-3 text-xs font-bold leading-5 text-[var(--missio-text-main)] dark:bg-white/5">
                      {closure.manager_note}
                    </div>
                  )}

                  <div className="mt-3 grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => void openDetail(closure)}
                      className="flex min-h-11 items-center justify-center gap-2 rounded-2xl bg-cyan-500 px-4 py-2 text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/20 transition active:scale-95"
                    >
                      <Eye size={17} />
                      {t("boss.report.detail")}
                    </button>

                    <PdfDownloadButton
                      compact
                      closureId={closure.id}
                      isDownloading={downloadingPdfClosureId === closure.id}
                      onDownload={handleDownloadPdf}
                    />
                  </div>
                </article>
              )
            })}
          </div>
        )}
      </section>

      {selectedClosure && (
        <ReportsDetailModal
          closure={selectedClosure}
          isLoading={isDetailLoading}
          isPdfDownloading={downloadingPdfClosureId === selectedClosure.id}
          onClose={() => setSelectedClosure(null)}
          onDownloadPdf={handleDownloadPdf}
        />
      )}
    </div>
  )
}
