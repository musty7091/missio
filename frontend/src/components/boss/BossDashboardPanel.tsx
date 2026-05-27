import { useEffect, useMemo, useState, type ReactNode } from "react"
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  ClipboardCheck,
  RefreshCw,
  ShieldCheck,
  UsersRound,
  XCircle,
} from "lucide-react"
import { useTranslation, type TranslationKey } from "../../i18n/language"

import {
  listDailyOperationClosures,
  type DailyOperationClosure,
} from "../../services/dailyClosureService"
import { listBusinessTasks } from "../../services/taskService"
import type { TodayTask } from "../../types/task"
import { mapApiTaskToTodayTask } from "../../utils/apiTaskMapper"
import { BossTaskAssignCard } from "./BossTaskAssignCard"

type BossDashboardPanelProps = {
  businessId: number | null
  onOpenApprovals: () => void
  onOpenReports: () => void
}

type StaffSummaryRow = {
  key: string
  name: string
  username: string | null
  total: number
  completed: number
  open: number
  approvalWaiting: number
  rejected: number
}

function getLocalTodayDateKey() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, "0")
  const day = String(now.getDate()).padStart(2, "0")

  return `${year}-${month}-${day}`
}

function formatDateTime(
  value: string | null,
  language: "tr" | "en",
  t: (key: TranslationKey) => string,
) {
  if (!value) {
    return t("boss.summary.date.none")
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return t("boss.summary.date.none")
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
  if (status === "closed_clean") {
    return t("boss.summary.closure.clean")
  }

  if (status === "closed_with_issues") {
    return t("boss.summary.closure.withIssues")
  }

  if (status === "closed") {
    return t("boss.summary.closure.closed")
  }

  return t("boss.summary.closure.record")
}

function isTaskCompletedOrClosed(task: TodayTask) {
  if (task.status === "approved") {
    return true
  }

  if (task.status === "completed" && !task.requiresManagerApproval) {
    return true
  }

  return false
}

function isApprovalWaiting(task: TodayTask) {
  return task.status === "completed" && task.requiresManagerApproval
}

function isProblemTask(task: TodayTask) {
  return (
    task.status === "assigned" ||
    task.status === "in_progress" ||
    task.status === "rejected" ||
    isApprovalWaiting(task)
  )
}

function getProblemLabel(
  task: TodayTask,
  t: (key: TranslationKey) => string,
) {
  if (task.status === "assigned") {
    return t("boss.summary.problem.waiting")
  }

  if (task.status === "in_progress") {
    return t("boss.summary.problem.inProgress")
  }

  if (task.status === "rejected") {
    return t("boss.summary.problem.rejected")
  }

  if (isApprovalWaiting(task)) {
    return t("boss.summary.problem.approval")
  }

  return t("boss.summary.problem.audit")
}

function getStaffRows(tasks: TodayTask[]) {
  const rows = new Map<string, StaffSummaryRow>()

  tasks.forEach((task) => {
    const key =
      task.assignedToUserId !== null
        ? String(task.assignedToUserId)
        : `unassigned-${task.id}`

    const existingRow = rows.get(key)

    const row =
      existingRow ??
      ({
        key,
        name:
          task.assignedToUserFullName ||
          task.assignedToUsername ||
          "Unassigned staff",
        username: task.assignedToUsername,
        total: 0,
        completed: 0,
        open: 0,
        approvalWaiting: 0,
        rejected: 0,
      } satisfies StaffSummaryRow)

    row.total += 1

    if (isTaskCompletedOrClosed(task)) {
      row.completed += 1
    }

    if (
      task.status === "assigned" ||
      task.status === "in_progress" ||
      task.status === "rejected"
    ) {
      row.open += 1
    }

    if (isApprovalWaiting(task)) {
      row.approvalWaiting += 1
    }

    if (task.status === "rejected") {
      row.rejected += 1
    }

    rows.set(key, row)
  })

  return Array.from(rows.values()).sort((firstRow, secondRow) => {
    const firstProblemCount =
      firstRow.open + firstRow.approvalWaiting + firstRow.rejected
    const secondProblemCount =
      secondRow.open + secondRow.approvalWaiting + secondRow.rejected

    return secondProblemCount - firstProblemCount
  })
}

function MetricCard({
  label,
  value,
  helper,
  icon,
  tone,
}: {
  label: string
  value: string | number
  helper: string
  icon: ReactNode
  tone: "cyan" | "emerald" | "amber" | "rose"
}) {
  const toneClassName =
    tone === "emerald"
      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200"
      : tone === "amber"
        ? "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-200"
        : tone === "rose"
          ? "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-200"
          : "bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200"

  return (
    <div className="rounded-[1.35rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-3">
        <p className="text-[0.68rem] font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
          {label}
        </p>

        <div className={`flex h-10 w-10 items-center justify-center rounded-2xl ${toneClassName}`}>
          {icon}
        </div>
      </div>

      <p className="text-2xl font-black text-[var(--missio-text-main)]">{value}</p>
      <p className="mt-1 text-xs font-bold leading-5 text-[var(--missio-text-muted)]">
        {helper}
      </p>
    </div>
  )
}

export function BossDashboardPanel({
  businessId,
  onOpenApprovals,
  onOpenReports,
}: BossDashboardPanelProps) {
  const { language, t } = useTranslation()
  const todayKey = getLocalTodayDateKey()
  const [tasks, setTasks] = useState<TodayTask[]>([])
  const [closures, setClosures] = useState<DailyOperationClosure[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  async function loadDashboard(
    options: {
      showLoading?: boolean
      showError?: boolean
    } = {},
  ) {
    const showLoading = options.showLoading ?? true
    const showError = options.showError ?? true

    if (!businessId) {
      setTasks([])
      setClosures([])
      setErrorMessage(t("boss.summary.error.noBusiness"))
      return
    }

    if (showLoading) {
      setIsLoading(true)
    }

    if (showError) {
      setErrorMessage(null)
    }

    try {
      const [taskResponse, closureResponse] = await Promise.all([
        listBusinessTasks({
          businessId,
          taskDate: todayKey,
          limit: 500,
          offset: 0,
        }),
        listDailyOperationClosures({
          businessId,
          limit: 10,
          offset: 0,
        }),
      ])

      setTasks(taskResponse.tasks.map(mapApiTaskToTodayTask))
      setClosures(closureResponse.closures)
      setErrorMessage(null)
    } catch (error) {
      if (showError) {
        if (error instanceof Error) {
          setErrorMessage(error.message)
        } else {
          setErrorMessage(t("boss.summary.error.loadFailed"))
        }
      }
    } finally {
      if (showLoading) {
        setIsLoading(false)
      }
    }
  }

  useEffect(() => {
    void loadDashboard()
  }, [businessId])

  useEffect(() => {
    if (!businessId) {
      return
    }

    function refreshDashboardWhenVisible() {
      if (document.visibilityState === "visible") {
        void loadDashboard({
          showLoading: false,
          showError: false,
        })
      }
    }

    const intervalId = window.setInterval(refreshDashboardWhenVisible, 10000)

    window.addEventListener("focus", refreshDashboardWhenVisible)
    document.addEventListener("visibilitychange", refreshDashboardWhenVisible)

    return () => {
      window.clearInterval(intervalId)
      window.removeEventListener("focus", refreshDashboardWhenVisible)
      document.removeEventListener("visibilitychange", refreshDashboardWhenVisible)
    }
  }, [businessId, todayKey])

  const todayClosure = useMemo(
    () => closures.find((closure) => closure.closure_date === todayKey) ?? null,
    [closures, todayKey],
  )

  const completedCount = tasks.filter(isTaskCompletedOrClosed).length
  const approvalWaitingCount = tasks.filter(isApprovalWaiting).length
  const problemTasks = tasks.filter(isProblemTask)
  const rejectedCount = tasks.filter((task) => task.status === "rejected").length
  const staffRows = useMemo(() => getStaffRows(tasks), [tasks])

  const closureStatusText = todayClosure
    ? getClosureStatusLabel(todayClosure.status, t)
    : t("boss.summary.closure.waiting")

  const closureStatusClassName =
    todayClosure?.status === "closed_with_issues"
      ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200"
      : todayClosure
        ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200"
        : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200"

  return (
    <div className="space-y-4">
      <section className="rounded-[2rem] bg-gradient-to-br from-slate-950 via-slate-900 to-cyan-950 p-4 text-white shadow-xl shadow-slate-950/20">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-black text-cyan-100">
              <ShieldCheck size={14} />
              {t("boss.summary.hero.badge")}
            </div>

            <h1 className="text-2xl font-black tracking-tight">
              {t("boss.summary.hero.title")}
            </h1>

            <p className="mt-2 max-w-sm text-sm font-bold leading-6 text-slate-300">
              {t("boss.summary.hero.description")}
            </p>
          </div>

          <button
            type="button"
            onClick={() => void loadDashboard()}
            disabled={isLoading}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/10 text-cyan-100 transition active:scale-95 disabled:opacity-60"
            aria-label={t("boss.summary.refresh")}
          >
            <RefreshCw className={isLoading ? "animate-spin" : ""} size={19} />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-2xl bg-white/10 px-3 py-3">
            <p className="text-2xl font-black">{tasks.length}</p>
            <p className="mt-1 text-[0.68rem] font-bold text-slate-300">
              {t("boss.summary.metric.todayTask")}
            </p>
          </div>

          <div className="rounded-2xl bg-white/10 px-3 py-3">
            <p className="text-2xl font-black">{completedCount}</p>
            <p className="mt-1 text-[0.68rem] font-bold text-slate-300">
              {t("boss.summary.metric.completed")}
            </p>
          </div>
        </div>

        <div className="mt-3 rounded-2xl bg-white/10 px-3 py-3">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.14em] text-slate-400">
                {t("boss.summary.closure.title")}
              </p>
              <p className="mt-1 text-sm font-black text-white">
                {closureStatusText}
              </p>
            </div>

            <span className={`rounded-full px-3 py-1 text-xs font-black ${closureStatusClassName}`}>
              {todayClosure
                ? t("boss.summary.closure.reportReady")
                : t("boss.summary.closure.reportWaiting")}
            </span>
          </div>

          {todayClosure ? (
            <p className="mt-2 text-xs font-bold leading-5 text-slate-300">
              {t("boss.summary.closure.closedBy")}: {todayClosure.closed_by_user_full_name} ·{" "}
              {formatDateTime(todayClosure.closed_at_utc, language, t)}
            </p>
          ) : (
            <button
              type="button"
              onClick={onOpenReports}
              className="mt-3 flex min-h-11 w-full items-center justify-center gap-2 rounded-2xl bg-cyan-400 px-4 py-2 text-sm font-black text-slate-950 shadow-lg shadow-cyan-400/20 transition active:scale-95"
            >
              <BarChart3 size={17} />
              {t("boss.summary.closure.goReport")}
            </button>
          )}
        </div>
      </section>

      {errorMessage && (
        <div className="rounded-[1.35rem] border border-rose-200 bg-rose-50 p-3 text-sm font-black text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
          {errorMessage}
        </div>
      )}

      <BossTaskAssignCard
        businessId={businessId}
        onChanged={() => void loadDashboard()}
      />

      <section className="grid grid-cols-2 gap-2.5">
        <MetricCard
          label={t("boss.summary.cards.open")}
          value={problemTasks.length}
          helper={t("boss.summary.cards.openDesc")}
          icon={<AlertTriangle size={19} />}
          tone={problemTasks.length > 0 ? "amber" : "emerald"}
        />

        <MetricCard
          label={t("boss.summary.cards.approval")}
          value={approvalWaitingCount}
          helper={t("boss.summary.cards.approvalDesc")}
          icon={<ClipboardCheck size={19} />}
          tone={approvalWaitingCount > 0 ? "amber" : "emerald"}
        />

        <MetricCard
          label={t("boss.summary.cards.rejected")}
          value={rejectedCount}
          helper={t("boss.summary.cards.rejectedDesc")}
          icon={<XCircle size={19} />}
          tone={rejectedCount > 0 ? "rose" : "emerald"}
        />

        <MetricCard
          label={t("boss.summary.cards.staff")}
          value={staffRows.length}
          helper={t("boss.summary.cards.staffDesc")}
          icon={<UsersRound size={19} />}
          tone="cyan"
        />
      </section>

      <section className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
              {t("boss.summary.audit.eyebrow")}
            </p>
            <h2 className="mt-1 text-base font-black text-[var(--missio-text-main)]">
              {t("boss.summary.audit.title")}
            </h2>
          </div>

          <button
            type="button"
            onClick={onOpenApprovals}
            className="rounded-full bg-[var(--missio-page-bg)] px-3 py-1.5 text-xs font-black text-[var(--missio-text-main)]"
          >
            {t("boss.summary.audit.goApproval")}
          </button>
        </div>

        {problemTasks.length === 0 ? (
          <div className="flex items-center gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-emerald-100 dark:bg-emerald-900">
              <CheckCircle2 size={20} />
            </div>

            <div>
              <p className="text-sm font-black">{t("boss.summary.audit.cleanTitle")}</p>
              <p className="mt-1 text-xs font-bold">
                {t("boss.summary.audit.cleanDescription")}
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            {problemTasks.slice(0, 5).map((task) => (
              <div
                key={task.id}
                className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-black text-[var(--missio-text-main)]">
                      {task.title}
                    </p>
                    <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
                      {task.assignedToUserFullName ||
                        task.assignedToUsername ||
                        t("boss.summary.audit.noStaff")}
                    </p>
                  </div>

                  <span className="rounded-full bg-amber-100 px-2.5 py-1 text-[0.65rem] font-black text-amber-800 dark:bg-amber-950 dark:text-amber-200">
                    {getProblemLabel(task, t)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
              {t("boss.summary.staff.eyebrow")}
            </p>
            <h2 className="mt-1 text-base font-black text-[var(--missio-text-main)]">
              {t("boss.summary.staff.title")}
            </h2>
          </div>

          <BarChart3 size={20} className="text-cyan-500" />
        </div>

        {staffRows.length === 0 ? (
          <div className="rounded-2xl bg-[var(--missio-page-bg)] p-4 text-sm font-bold leading-6 text-[var(--missio-text-muted)]">
            {t("boss.summary.staff.empty")}
          </div>
        ) : (
          <div className="space-y-2">
            {staffRows.slice(0, 6).map((row) => (
              <div
                key={row.key}
                className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-3"
              >
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-cyan-100 text-sm font-black text-cyan-800 dark:bg-cyan-950 dark:text-cyan-200">
                      {row.name.slice(0, 2).toLocaleUpperCase(language === "tr" ? "tr-TR" : "en-GB")}
                    </div>

                    <div>
                      <p className="text-sm font-black text-[var(--missio-text-main)]">
                        {row.name}
                      </p>
                      {row.username && (
                        <p className="mt-0.5 text-xs font-bold text-[var(--missio-text-muted)]">
                          @{row.username}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="rounded-2xl bg-[var(--missio-card-bg)] px-3 py-2 text-center">
                    <p className="text-base font-black text-[var(--missio-text-main)]">
                      {row.total}
                    </p>
                    <p className="text-[0.62rem] font-bold text-[var(--missio-text-muted)]">
                      {t("boss.summary.staff.task")}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="rounded-xl bg-white/60 px-2 py-2 dark:bg-white/5">
                    <p className="text-sm font-black text-emerald-600">
                      {row.completed}
                    </p>
                    <p className="text-[0.62rem] font-bold text-[var(--missio-text-muted)]">
                      {t("boss.summary.staff.done")}
                    </p>
                  </div>

                  <div className="rounded-xl bg-white/60 px-2 py-2 dark:bg-white/5">
                    <p className="text-sm font-black text-amber-600">
                      {row.open + row.approvalWaiting}
                    </p>
                    <p className="text-[0.62rem] font-bold text-[var(--missio-text-muted)]">
                      {t("boss.summary.staff.audit")}
                    </p>
                  </div>

                  <div className="rounded-xl bg-white/60 px-2 py-2 dark:bg-white/5">
                    <p className="text-sm font-black text-rose-600">
                      {row.rejected}
                    </p>
                    <p className="text-[0.62rem] font-bold text-[var(--missio-text-muted)]">
                      {t("boss.summary.staff.rejected")}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
