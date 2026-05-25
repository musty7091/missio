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
    return "Gün kapanışııldı"
  }

  return "Kapanış kaydı"
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

function getProblemLabel(task: TodayTask) {
  if (task.status === "assigned") {
    return "Bekliyor"
  }

  if (task.status === "in_progress") {
    return "Devam ediyor"
  }

  if (task.status === "rejected") {
    return "Reddedildi"
  }

  if (isApprovalWaiting(task)) {
    return "Onay bekliyor"
  }

  return "Denetim"
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
          "Atanmamış personel",
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
  const todayKey = getLocalTodayDateKey()
  const [tasks, setTasks] = useState<TodayTask[]>([])
  const [closures, setClosures] = useState<DailyOperationClosure[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  async function loadDashboard() {
    if (!businessId) {
      setTasks([])
      setClosures([])
      setErrorMessage("Bu kullanıcı için işletme bilgisi bulunamadı.")
      return
    }

    setIsLoading(true)
    setErrorMessage(null)

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
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("İşletme sahibi ekranı yüklenemedi.")
      }
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadDashboard()
  }, [businessId])

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
    ? getClosureStatusLabel(todayClosure.status)
    : "Kapanış bekliyor"

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
              İşletme sahibi kontrol merkezi
            </div>

            <h1 className="text-2xl font-black tracking-tight">
              İşletme özeti
            </h1>

            <p className="mt-2 max-w-sm text-sm font-bold leading-6 text-slate-300">
              Günün görev, onay, personel ve kapanış durumunu tek ekrandan takip et.
            </p>
          </div>

          <button
            type="button"
            onClick={() => void loadDashboard()}
            disabled={isLoading}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/10 text-cyan-100 transition active:scale-95 disabled:opacity-60"
            aria-label="Yenile"
          >
            <RefreshCw className={isLoading ? "animate-spin" : ""} size={19} />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-2xl bg-white/10 px-3 py-3">
            <p className="text-2xl font-black">{tasks.length}</p>
            <p className="mt-1 text-[0.68rem] font-bold text-slate-300">
              Bugünkü görev
            </p>
          </div>

          <div className="rounded-2xl bg-white/10 px-3 py-3">
            <p className="text-2xl font-black">{completedCount}</p>
            <p className="mt-1 text-[0.68rem] font-bold text-slate-300">
              Tamamlanan
            </p>
          </div>
        </div>

        <div className="mt-3 rounded-2xl bg-white/10 px-3 py-3">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.14em] text-slate-400">
                Gün kapanışı
              </p>
              <p className="mt-1 text-sm font-black text-white">
                {closureStatusText}
              </p>
            </div>

            <span className={`rounded-full px-3 py-1 text-xs font-black ${closureStatusClassName}`}>
              {todayClosure ? "Rapor hazır" : "Rapor bekliyor"}
            </span>
          </div>

          {todayClosure ? (
            <p className="mt-2 text-xs font-bold leading-5 text-slate-300">
              Kapatan: {todayClosure.closed_by_user_full_name} · {formatDateTime(todayClosure.closed_at_utc)}
            </p>
          ) : (
            <button
              type="button"
              onClick={onOpenReports}
              className="mt-3 flex min-h-11 w-full items-center justify-center gap-2 rounded-2xl bg-cyan-400 px-4 py-2 text-sm font-black text-slate-950 shadow-lg shadow-cyan-400/20 transition active:scale-95"
            >
              <BarChart3 size={17} />
              Gün kapanışı raporuna git
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
          label="Açık iş"
          value={problemTasks.length}
          helper="Bekleyen, işlemde, red veya onay"
          icon={<AlertTriangle size={19} />}
          tone={problemTasks.length > 0 ? "amber" : "emerald"}
        />

        <MetricCard
          label="Onay"
          value={approvalWaitingCount}
          helper="Yönetici/işletme sahibi onayı bekleyen"
          icon={<ClipboardCheck size={19} />}
          tone={approvalWaitingCount > 0 ? "amber" : "emerald"}
        />

        <MetricCard
          label="Red"
          value={rejectedCount}
          helper="Düzeltilmesi gereken görev"
          icon={<XCircle size={19} />}
          tone={rejectedCount > 0 ? "rose" : "emerald"}
        />

        <MetricCard
          label="Personel"
          value={staffRows.length}
          helper="Bugün görev alan kişi"
          icon={<UsersRound size={19} />}
          tone="cyan"
        />
      </section>

      <section className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
              Denetim
            </p>
            <h2 className="mt-1 text-base font-black text-[var(--missio-text-main)]">
              İnceleme gereken işler
            </h2>
          </div>

          <button
            type="button"
            onClick={onOpenApprovals}
            className="rounded-full bg-[var(--missio-page-bg)] px-3 py-1.5 text-xs font-black text-[var(--missio-text-main)]"
          >
            Onaya git
          </button>
        </div>

        {problemTasks.length === 0 ? (
          <div className="flex items-center gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-emerald-100 dark:bg-emerald-900">
              <CheckCircle2 size={20} />
            </div>

            <div>
              <p className="text-sm font-black">Kritik açık iş görünmüyor</p>
              <p className="mt-1 text-xs font-bold">
                Bugünkü operasyon kontrol altında.
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
                      {task.assignedToUserFullName || task.assignedToUsername || "Personel yok"}
                    </p>
                  </div>

                  <span className="rounded-full bg-amber-100 px-2.5 py-1 text-[0.65rem] font-black text-amber-800 dark:bg-amber-950 dark:text-amber-200">
                    {getProblemLabel(task)}
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
              Personel
            </p>
            <h2 className="mt-1 text-base font-black text-[var(--missio-text-main)]">
              Bugünkü personel özeti
            </h2>
          </div>

          <BarChart3 size={20} className="text-cyan-500" />
        </div>

        {staffRows.length === 0 ? (
          <div className="rounded-2xl bg-[var(--missio-page-bg)] p-4 text-sm font-bold leading-6 text-[var(--missio-text-muted)]">
            Bugün personel görevi görünmüyor.
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
                      {row.name.slice(0, 2).toLocaleUpperCase("tr-TR")}
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
                      görev
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="rounded-xl bg-white/60 px-2 py-2 dark:bg-white/5">
                    <p className="text-sm font-black text-emerald-600">
                      {row.completed}
                    </p>
                    <p className="text-[0.62rem] font-bold text-[var(--missio-text-muted)]">
                      Tamam
                    </p>
                  </div>

                  <div className="rounded-xl bg-white/60 px-2 py-2 dark:bg-white/5">
                    <p className="text-sm font-black text-amber-600">
                      {row.open + row.approvalWaiting}
                    </p>
                    <p className="text-[0.62rem] font-bold text-[var(--missio-text-muted)]">
                      Denetim
                    </p>
                  </div>

                  <div className="rounded-xl bg-white/60 px-2 py-2 dark:bg-white/5">
                    <p className="text-sm font-black text-rose-600">
                      {row.rejected}
                    </p>
                    <p className="text-[0.62rem] font-bold text-[var(--missio-text-muted)]">
                      Red
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
