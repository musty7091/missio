import {
  AlertTriangle,
  Camera,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  FileCheck2,
  Loader2,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  UserRound,
  UsersRound,
  XCircle,
} from "lucide-react"
import { useEffect, useMemo, useState, type ReactNode } from "react"
import {
  createDailyOperationClosure,
  listDailyOperationClosures,
  type DailyOperationClosure,
} from "../../services/dailyClosureService"
import { listBusinessTasks } from "../../services/taskService"
import type { TodayTask } from "../../types/task"
import { mapApiTaskToTodayTask } from "../../utils/apiTaskMapper"
import { getPriorityLabel, getStatusLabel } from "../../utils/taskLabels"

type ReportsPanelProps = {
  tasks: TodayTask[]
  role: string
  businessId: number | null
  onOpenTaskDetails: (task: TodayTask) => void
}

type ControlCheckStatus = "success" | "warning" | "info" | "danger"

type StaffReportRow = {
  key: string
  name: string
  username: string | null
  total: number
  completed: number
  open: number
  approvalPending: number
  rejected: number
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

  return "Kapanış kaydı"
}

function getClosureStatusMessage(status: string) {
  if (status === "closed_clean") {
    return "Bugün temiz kapanış olarak kapatıldı."
  }

  if (status === "closed_with_issues") {
    return "Bugün sorunlu kapanış olarak kapatıldı."
  }

  return "Bugünün gün sonu raporu oluşturuldu."
}

function canCurrentRoleCloseDay(role: string) {
  return role === "manager" || role === "boss" || role === "business_owner"
}

function getLocalTodayDateKey() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, "0")
  const day = String(now.getDate()).padStart(2, "0")

  return `${year}-${month}-${day}`
}

function isCompletedTask(task: TodayTask) {
  return task.status === "completed" || task.status === "approved"
}

function isApprovedOrClosed(task: TodayTask) {
  return (
    task.status === "approved" ||
    task.status === "cancelled" ||
    (task.status === "completed" && !task.requiresManagerApproval)
  )
}

function isOpenTask(task: TodayTask) {
  return (
    task.status === "assigned" ||
    task.status === "in_progress" ||
    task.status === "rejected"
  )
}

function isApprovalPendingTask(task: TodayTask) {
  return task.status === "completed" && task.requiresManagerApproval
}

function getPercent(value: number, total: number) {
  if (total <= 0) {
    return 0
  }

  return Math.round((value / total) * 100)
}

function getAssigneeName(task: TodayTask) {
  if (task.assignedToUserFullName) {
    return task.assignedToUserFullName
  }

  if (task.assignedToUsername) {
    return task.assignedToUsername
  }

  if (task.assignedToUserId) {
    return `Personel ID #${task.assignedToUserId}`
  }

  return "Personel bilgisi yok"
}

function getStaffReportRows(tasks: TodayTask[]) {
  const groups = new Map<string, StaffReportRow>()

  for (const task of tasks) {
    const name = getAssigneeName(task)
    const key = task.assignedToUserId ? `user-${task.assignedToUserId}` : `name-${name}`

    const row =
      groups.get(key) ??
      {
        key,
        name,
        username: task.assignedToUsername,
        total: 0,
        completed: 0,
        open: 0,
        approvalPending: 0,
        rejected: 0,
      }

    row.total += 1

    if (isCompletedTask(task)) {
      row.completed += 1
    }

    if (isOpenTask(task)) {
      row.open += 1
    }

    if (isApprovalPendingTask(task)) {
      row.approvalPending += 1
    }

    if (task.status === "rejected") {
      row.rejected += 1
    }

    groups.set(key, row)
  }

  return Array.from(groups.values()).sort((firstRow, secondRow) =>
    firstRow.name.localeCompare(secondRow.name, "tr-TR"),
  )
}

function MetricCard({
  title,
  value,
  description,
  icon,
}: {
  title: string
  value: string | number
  description: string
  icon: ReactNode
}) {
  return (
    <div className="rounded-[1.4rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[0.68rem] font-black uppercase tracking-[0.13em] text-[var(--missio-text-muted)]">
            {title}
          </p>

          <p className="mt-2 text-2xl font-black leading-none text-[var(--missio-text-main)]">
            {value}
          </p>

          <p className="mt-2 text-xs font-bold leading-5 text-[var(--missio-text-muted)]">
            {description}
          </p>
        </div>

        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
          {icon}
        </div>
      </div>
    </div>
  )
}

function getCheckStyles(status: ControlCheckStatus) {
  if (status === "success") {
    return {
      box: "border-emerald-200 bg-emerald-50 dark:border-emerald-900 dark:bg-emerald-950/30",
      icon: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200",
      text: "text-emerald-950 dark:text-emerald-100",
      muted: "text-emerald-800 dark:text-emerald-200",
    }
  }

  if (status === "danger") {
    return {
      box: "border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950/30",
      icon: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-200",
      text: "text-red-950 dark:text-red-100",
      muted: "text-red-800 dark:text-red-200",
    }
  }

  if (status === "warning") {
    return {
      box: "border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/30",
      icon: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-200",
      text: "text-amber-950 dark:text-amber-100",
      muted: "text-amber-800 dark:text-amber-200",
    }
  }

  return {
    box: "border-cyan-200 bg-cyan-50 dark:border-cyan-900 dark:bg-cyan-950/30",
    icon: "bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200",
    text: "text-cyan-950 dark:text-cyan-100",
    muted: "text-cyan-800 dark:text-cyan-200",
  }
}

function ControlCheckCard({
  status,
  icon,
  title,
  description,
}: {
  status: ControlCheckStatus
  icon: ReactNode
  title: string
  description: string
}) {
  const styles = getCheckStyles(status)

  return (
    <div className={`rounded-[1.4rem] border p-3 ${styles.box}`}>
      <div className="flex items-start gap-3">
        <div
          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl ${styles.icon}`}
        >
          {icon}
        </div>

        <div className="min-w-0">
          <h3 className={`text-sm font-black ${styles.text}`}>{title}</h3>

          <p className={`mt-1 text-xs font-bold leading-5 ${styles.muted}`}>
            {description}
          </p>
        </div>
      </div>
    </div>
  )
}

function ControlTaskRow({
  task,
  onOpenTaskDetails,
}: {
  task: TodayTask
  onOpenTaskDetails?: (task: TodayTask) => void
}) {
  const clickable = Boolean(onOpenTaskDetails)

  const content = (
    <>
      <div className="min-w-0">
        <div className="mb-1.5 flex flex-wrap gap-1.5">
          <span
            className={
              task.taskType === "routine"
                ? "rounded-full bg-cyan-100 px-2 py-0.5 text-[0.6rem] font-black text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200"
                : "rounded-full bg-violet-100 px-2 py-0.5 text-[0.6rem] font-black text-violet-700 dark:bg-violet-950 dark:text-violet-200"
            }
          >
            {task.taskType === "routine" ? "Rutin" : "Ekstra"}
          </span>

          <span className="rounded-full bg-[var(--missio-card-bg)] px-2 py-0.5 text-[0.6rem] font-black text-[var(--missio-text-muted)]">
            {getStatusLabel(task.status)}
          </span>

          <span className="rounded-full bg-[var(--missio-card-bg)] px-2 py-0.5 text-[0.6rem] font-black text-[var(--missio-text-muted)]">
            {getPriorityLabel(task.priority)}
          </span>

          {task.requiresManagerApproval && (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[0.6rem] font-black text-amber-700 dark:bg-amber-950 dark:text-amber-200">
              Onay
            </span>
          )}
        </div>

        <p className="truncate text-sm font-black text-[var(--missio-text-main)]">
          {task.title}
        </p>

        <p className="mt-1 line-clamp-1 text-xs font-bold text-[var(--missio-text-muted)]">
          {getAssigneeName(task)}
        </p>
      </div>

      {clickable && <ChevronRight className="shrink-0 text-[var(--missio-text-muted)]" size={18} />}
    </>
  )

  if (!clickable) {
    return (
      <div className="flex w-full items-center justify-between gap-3 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-3 text-left">
        {content}
      </div>
    )
  }

  return (
    <button
      type="button"
      onClick={() => onOpenTaskDetails?.(task)}
      className="flex w-full items-center justify-between gap-3 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-3 text-left transition active:scale-[0.99]"
    >
      {content}
    </button>
  )
}

function StaffControlPanel({
  tasks,
  onOpenTaskDetails,
}: {
  tasks: TodayTask[]
  onOpenTaskDetails: (task: TodayTask) => void
}) {
  const totalCount = tasks.length
  const completedTasks = tasks.filter(isCompletedTask)
  const openTasks = tasks.filter(isOpenTask)
  const waitingTasks = tasks.filter((task) => task.status === "assigned")
  const activeTasks = tasks.filter((task) => task.status === "in_progress")
  const rejectedTasks = tasks.filter((task) => task.status === "rejected")
  const photoRequiredOpenTasks = tasks.filter(
    (task) => task.requiresPhoto && isOpenTask(task),
  )
  const approvalWaitingTasks = tasks.filter(isApprovalPendingTask)

  const blockingTasks = [
    ...rejectedTasks,
    ...activeTasks,
    ...photoRequiredOpenTasks,
    ...waitingTasks,
  ].filter((task, index, list) => list.findIndex((item) => item.id === task.id) === index)

  const completionRate = getPercent(completedTasks.length, totalCount)
  const isReadyToClose =
    totalCount > 0 &&
    openTasks.length === 0 &&
    activeTasks.length === 0 &&
    photoRequiredOpenTasks.length === 0

  return (
    <section className="flex flex-1 flex-col pb-24">
      <div
        className={
          isReadyToClose
            ? "mb-4 rounded-[1.7rem] bg-emerald-950 p-4 text-white shadow-xl shadow-emerald-950/15"
            : "mb-4 rounded-[1.7rem] bg-slate-950 p-4 text-white shadow-xl shadow-slate-950/15"
        }
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-black text-cyan-200">
              <ShieldCheck size={14} />
              Kontrol
            </div>

            <h2 className="mt-3 text-2xl font-black leading-tight">
              {isReadyToClose ? "Bugün kapatılabilir" : "Eksik kontrolü"}
            </h2>

            <p className="mt-2 text-sm font-semibold leading-5 text-slate-300">
              Gün bitmeden açık, işlemde veya kanıt isteyen görevleri kontrol et.
            </p>
          </div>

          <div className="shrink-0 rounded-2xl bg-cyan-300 px-3 py-2 text-center text-slate-950">
            <p className="text-lg font-black leading-none">%{completionRate}</p>
            <p className="mt-1 text-[0.62rem] font-black">tamam</p>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-3 gap-2">
          <div className="rounded-2xl bg-white/10 px-3 py-2">
            <p className="text-xl font-black leading-none">{openTasks.length}</p>
            <p className="mt-1 text-[0.64rem] font-bold text-slate-300">Açık</p>
          </div>

          <div className="rounded-2xl bg-white/10 px-3 py-2">
            <p className="text-xl font-black leading-none">{activeTasks.length}</p>
            <p className="mt-1 text-[0.64rem] font-bold text-slate-300">İşlemde</p>
          </div>

          <div className="rounded-2xl bg-white/10 px-3 py-2">
            <p className="text-xl font-black leading-none">{photoRequiredOpenTasks.length}</p>
            <p className="mt-1 text-[0.64rem] font-bold text-slate-300">Kanıt</p>
          </div>
        </div>
      </div>

      {totalCount === 0 ? (
        <div className="flex flex-1 items-center justify-center rounded-[1.7rem] border border-dashed border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-6 text-center">
          <div>
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-3xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
              <ClipboardCheck size={28} />
            </div>

            <h3 className="mt-4 text-lg font-black">Kontrol edilecek görev yok</h3>

            <p className="mt-2 text-sm font-semibold leading-6 text-[var(--missio-text-muted)]">
              Bugüne görev atandığında gün sonu kontrolün burada oluşacak.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-2.5">
            <ControlCheckCard
              status={openTasks.length === 0 ? "success" : "warning"}
              icon={openTasks.length === 0 ? <CheckCircle2 size={22} /> : <AlertTriangle size={22} />}
              title={openTasks.length === 0 ? "Açık görev kalmadı" : `${openTasks.length} açık görev var`}
              description={
                openTasks.length === 0
                  ? "Bugünkü görevlerin tamamlanmış görünüyor."
                  : "Günü kapatmadan önce açık görevleri kontrol etmelisin."
              }
            />

            <ControlCheckCard
              status={approvalWaitingTasks.length === 0 ? "success" : "info"}
              icon={<FileCheck2 size={22} />}
              title={
                approvalWaitingTasks.length === 0
                  ? "Onay bekleyen görev yok"
                  : `${approvalWaitingTasks.length} görev yönetici onayında`
              }
              description={
                approvalWaitingTasks.length === 0
                  ? "Yönetici onayı bekleyen tamamlanmış görevin yok."
                  : "Bu görevler tamamlanmış, yönetici onayı bekliyor."
              }
            />
          </div>

          <div className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                  Hemen kontrol et
                </p>

                <h3 className="mt-1 text-base font-black text-[var(--missio-text-main)]">
                  Günü kapatmadan önce bakılacak işler
                </h3>
              </div>

              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-200">
                <ShieldAlert size={22} />
              </div>
            </div>

            {blockingTasks.length === 0 ? (
              <div className="rounded-2xl bg-emerald-50 p-3 text-sm font-bold text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-200">
                Kontrol gerektiren açık iş görünmüyor. Bugün kapatılabilir.
              </div>
            ) : (
              <div className="space-y-2">
                {blockingTasks.map((task) => (
                  <ControlTaskRow
                    key={task.id}
                    task={task}
                    onOpenTaskDetails={onOpenTaskDetails}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  )
}

function StaffReportCard({ row }: { row: StaffReportRow }) {
  const completionRate = getPercent(row.completed, row.total)

  return (
    <article className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-sm font-black text-cyan-800 dark:text-cyan-200">
          <UserRound size={21} />
        </div>

        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-black text-[var(--missio-text-main)]">
            {row.name}
          </h3>

          {row.username && (
            <p className="mt-0.5 truncate text-xs font-bold text-[var(--missio-text-muted)]">
              @{row.username}
            </p>
          )}
        </div>

        <div className="rounded-2xl bg-[var(--missio-page-bg)] px-3 py-2 text-center">
          <p className="text-base font-black leading-none text-[var(--missio-text-main)]">
            %{completionRate}
          </p>
          <p className="mt-1 text-[0.58rem] font-black text-[var(--missio-text-muted)]">
            tamam
          </p>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-4 gap-2 text-center">
        <div className="rounded-2xl bg-[var(--missio-page-bg)] px-2 py-2">
          <p className="text-sm font-black text-[var(--missio-text-main)]">{row.total}</p>
          <p className="text-[0.56rem] font-black text-[var(--missio-text-muted)]">Toplam</p>
        </div>

        <div className="rounded-2xl bg-[var(--missio-page-bg)] px-2 py-2">
          <p className="text-sm font-black text-emerald-600 dark:text-emerald-300">{row.completed}</p>
          <p className="text-[0.56rem] font-black text-[var(--missio-text-muted)]">Biten</p>
        </div>

        <div className="rounded-2xl bg-[var(--missio-page-bg)] px-2 py-2">
          <p className="text-sm font-black text-amber-600 dark:text-amber-300">{row.open}</p>
          <p className="text-[0.56rem] font-black text-[var(--missio-text-muted)]">Açık</p>
        </div>

        <div className="rounded-2xl bg-[var(--missio-page-bg)] px-2 py-2">
          <p className={row.rejected > 0 ? "text-sm font-black text-red-600 dark:text-red-300" : "text-sm font-black text-[var(--missio-text-main)]"}>
            {row.rejected}
          </p>
          <p className="text-[0.56rem] font-black text-[var(--missio-text-muted)]">Red</p>
        </div>
      </div>

      {row.approvalPending > 0 && (
        <div className="mt-3 rounded-2xl bg-cyan-50 px-3 py-2 text-xs font-black text-cyan-700 dark:bg-cyan-950/40 dark:text-cyan-200">
          {row.approvalPending} görev yönetici onayı bekliyor.
        </div>
      )}
    </article>
  )
}

function ManagementReportPanel({
  role,
  businessId,
}: {
  role: string
  businessId: number | null
}) {
  const [reportTasks, setReportTasks] = useState<TodayTask[]>([])
  const [closures, setClosures] = useState<DailyOperationClosure[]>([])
  const [closureNote, setClosureNote] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isClosingDay, setIsClosingDay] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const todayKey = getLocalTodayDateKey()

  async function loadReportTasks() {
    if (!businessId) {
      setReportTasks([])
      setErrorMessage("Bu kullanıcı için işletme bilgisi bulunamadı.")
      return
    }

    setIsLoading(true)
    setErrorMessage(null)
    setSuccessMessage(null)

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
          limit: 30,
          offset: 0,
        }),
      ])

      setReportTasks(taskResponse.tasks.map(mapApiTaskToTodayTask))
      setClosures(closureResponse.closures)
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Gün sonu raporu alınamadı.")
      }

      setReportTasks([])
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadReportTasks()
  }, [businessId])

  const todayClosure = useMemo(
    () => closures.find((closure) => closure.closure_date === todayKey) ?? null,
    [closures, todayKey],
  )

  const totalCount = reportTasks.length
  const completedTasks = reportTasks.filter(isCompletedTask)
  const approvedOrClosedTasks = reportTasks.filter(isApprovedOrClosed)
  const openTasks = reportTasks.filter(isOpenTask)
  const assignedTasks = reportTasks.filter((task) => task.status === "assigned")
  const activeTasks = reportTasks.filter((task) => task.status === "in_progress")
  const rejectedTasks = reportTasks.filter((task) => task.status === "rejected")
  const approvalWaitingTasks = reportTasks.filter(isApprovalPendingTask)
  const photoRequiredOpenTasks = reportTasks.filter(
    (task) => task.requiresPhoto && isOpenTask(task),
  )

  const blockingTasks = [
    ...rejectedTasks,
    ...approvalWaitingTasks,
    ...activeTasks,
    ...photoRequiredOpenTasks,
    ...assignedTasks,
  ].filter((task, index, list) => list.findIndex((item) => item.id === task.id) === index)

  const staffRows = useMemo(() => getStaffReportRows(reportTasks), [reportTasks])
  const completionRate = getPercent(completedTasks.length, totalCount)
  const closureRate = getPercent(approvedOrClosedTasks.length, totalCount)

  const canCloseDay =
    totalCount > 0 &&
    openTasks.length === 0 &&
    approvalWaitingTasks.length === 0 &&
    rejectedTasks.length === 0

  const hasTasksForClosure = totalCount > 0
  const closureHasIssues = hasTasksForClosure && !canCloseDay
  const canShowCloseButton = canCurrentRoleCloseDay(role)
  const isDayAlreadyClosed = todayClosure !== null

  async function handleCloseDay() {
    if (!businessId) {
      setErrorMessage("Bu kullanıcı için işletme bilgisi bulunamadı.")
      return
    }

    if (!canShowCloseButton) {
      setErrorMessage("Bu kullanıcı günü kapatamaz.")
      return
    }

    if (!hasTasksForClosure) {
      setErrorMessage("Bugün kapatılacak görev bulunamadı.")
      return
    }

    if (closureHasIssues && !closureNote.trim()) {
      setErrorMessage("Sorunlu gün kapanışında kapanış notu zorunludur.")
      return
    }

    setIsClosingDay(true)
    setErrorMessage(null)
    setSuccessMessage(null)

    try {
      const response = await createDailyOperationClosure(
        {
          closure_date: todayKey,
          manager_note: closureNote.trim() || null,
        },
        {
          businessId,
        },
      )

      setClosures((currentClosures) => [
        response.closure,
        ...currentClosures.filter((closure) => closure.id !== response.closure.id),
      ])
      setClosureNote("")
      setSuccessMessage(response.message)
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Gün kapatılamadı.")
      }
    } finally {
      setIsClosingDay(false)
    }
  }

  const roleTitle =
    role === "boss"
      ? "Patron gün sonu raporu"
      : role === "admin" || role === "super_admin"
        ? "Admin gün sonu raporu"
        : "Yönetici gün sonu raporu"

  return (
    <section className="flex flex-1 flex-col pb-24">
      <div
        className={
          canCloseDay
            ? "mb-4 rounded-[1.7rem] bg-emerald-950 p-4 text-white shadow-xl shadow-emerald-950/15"
            : "mb-4 rounded-[1.7rem] bg-slate-950 p-4 text-white shadow-xl shadow-slate-950/15"
        }
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-black text-cyan-200">
              <UsersRound size={14} />
              Raporlar
            </div>

            <h2 className="mt-3 text-2xl font-black leading-tight">{roleTitle}</h2>

            <p className="mt-2 text-sm font-semibold leading-5 text-slate-300">
              Bugünkü görevleri personel, onay ve eksik iş durumuna göre kontrol et.
            </p>
          </div>

          <button
            type="button"
            onClick={() => void loadReportTasks()}
            disabled={isLoading}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/10 text-cyan-200 transition active:scale-95 disabled:opacity-60"
            aria-label="Yenile"
            title="Yenile"
          >
            {isLoading ? <Loader2 className="animate-spin" size={19} /> : <RefreshCw size={19} />}
          </button>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-2">
          <div className="rounded-2xl bg-white/10 px-3 py-2">
            <p className="text-xl font-black leading-none">{totalCount}</p>
            <p className="mt-1 text-[0.64rem] font-bold text-slate-300">Toplam görev</p>
          </div>

          <div className="rounded-2xl bg-white/10 px-3 py-2">
            <p className="text-xl font-black leading-none">%{completionRate}</p>
            <p className="mt-1 text-[0.64rem] font-bold text-slate-300">Tamamlama</p>
          </div>
        </div>

        <div className="mt-2 space-y-3 rounded-2xl bg-white/10 px-3 py-3">
          <div>
            <p
              className={
                isDayAlreadyClosed && todayClosure?.status === "closed_with_issues"
                  ? "text-sm font-black text-amber-200"
                  : isDayAlreadyClosed
                    ? "text-sm font-black text-emerald-200"
                    : canCloseDay
                      ? "text-sm font-black text-emerald-200"
                      : hasTasksForClosure
                        ? "text-sm font-black text-amber-200"
                        : "text-sm font-black text-slate-300"
              }
            >
              {isDayAlreadyClosed && todayClosure
                ? getClosureStatusLabel(todayClosure.status)
                : canCloseDay
                  ? "Temiz kapanış yapılabilir."
                  : hasTasksForClosure
                    ? "Sorunlu kapanış yapılacak."
                    : "Kapatılacak görev yok."}
            </p>

            <p className="mt-1 text-[0.68rem] font-bold text-slate-300">
              Kapanış uygunluğu: %{closureRate}
            </p>
          </div>

          {isDayAlreadyClosed && todayClosure ? (
            <div
              className={
                todayClosure.status === "closed_with_issues"
                  ? "rounded-2xl bg-amber-50/95 p-3 text-sm font-bold leading-6 text-amber-900"
                  : "rounded-2xl bg-emerald-50/95 p-3 text-sm font-bold leading-6 text-emerald-900"
              }
            >
              <p>{getClosureStatusMessage(todayClosure.status)}</p>
              <p className="mt-1 text-xs">
                Kapatan: {todayClosure.closed_by_user_full_name} · {formatDateTime(todayClosure.closed_at_utc)}
              </p>
              {todayClosure.manager_note && (
                <p className="mt-2 rounded-xl bg-white/70 px-3 py-2 text-xs">
                  {todayClosure.manager_note}
                </p>
              )}
            </div>
          ) : canShowCloseButton ? (
            <div className="space-y-2">
              <textarea
                value={closureNote}
                onChange={(event) => setClosureNote(event.target.value)}
                placeholder={
                  closureHasIssues
                    ? "Sorunlu kapanış notu zorunlu. Örn: Personel eksikliği nedeniyle depo sayımı tamamlanamadı."
                    : "Kapanış notu yaz... Örn: Gün sorunsuz tamamlandı."
                }
                maxLength={5000}
                className="min-h-20 w-full resize-none rounded-2xl border border-white/20 bg-white/10 px-3 py-3 text-sm font-bold text-white outline-none placeholder:text-slate-300 focus:border-cyan-300"
              />

              <button
                type="button"
                onClick={() => void handleCloseDay()}
                disabled={!hasTasksForClosure || isClosingDay}
                className={
                  hasTasksForClosure
                    ? closureHasIssues
                      ? "flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-amber-500 px-4 py-3 text-sm font-black text-white shadow-lg shadow-amber-500/20 transition active:scale-95 disabled:cursor-wait disabled:opacity-60"
                      : "flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-emerald-500 px-4 py-3 text-sm font-black text-white shadow-lg shadow-emerald-500/20 transition active:scale-95 disabled:cursor-wait disabled:opacity-60"
                    : "flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-slate-300 px-4 py-3 text-sm font-black text-slate-600 opacity-70"
                }
              >
                {isClosingDay ? <Loader2 className="animate-spin" size={18} /> : <ShieldCheck size={18} />}
                Günü Kapat
              </button>

              {closureHasIssues && (
                <p className="rounded-2xl bg-amber-50/95 p-3 text-xs font-bold leading-5 text-amber-900">
                  Bu gün sorunlu kapanış olarak kaydedilecek. Açık, reddedilmiş veya onay bekleyen görevler rapora yansıyacak. Kapanış notu zorunludur.
                </p>
              )}
            </div>
          ) : (
            <p className="rounded-2xl bg-white/10 p-3 text-xs font-bold leading-5 text-slate-300">
              Bu kullanıcı günü kapatamaz.
            </p>
          )}
        </div>
      </div>

      {successMessage && (
        <div className="mb-3 rounded-[1.4rem] border border-emerald-200 bg-emerald-50 p-3 text-sm font-black text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
          {successMessage}
        </div>
      )}

      {errorMessage && (
        <div className="mb-3 rounded-[1.4rem] border border-red-200 bg-red-50 p-3 text-sm font-black text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
          {errorMessage}
        </div>
      )}

      {isLoading ? (
        <div className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 text-sm font-black text-[var(--missio-text-muted)]">
          Gün sonu raporu yükleniyor...
        </div>
      ) : totalCount === 0 ? (
        <div className="flex flex-1 items-center justify-center rounded-[1.7rem] border border-dashed border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-6 text-center">
          <div>
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-3xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
              <ClipboardCheck size={28} />
            </div>

            <h3 className="mt-4 text-lg font-black">Bugün raporlanacak görev yok</h3>

            <p className="mt-2 text-sm font-semibold leading-6 text-[var(--missio-text-muted)]">
              İşletmeye görev atandığında gün sonu raporu burada oluşacak.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-2.5">
            <MetricCard
              title="Tamamlanan"
              value={completedTasks.length}
              description="Tamamlanan veya onaylanan"
              icon={<CheckCircle2 size={22} />}
            />

            <MetricCard
              title="Açık"
              value={openTasks.length}
              description="Bekleyen, işlemde veya red"
              icon={<AlertTriangle size={22} />}
            />

            <MetricCard
              title="Onay"
              value={approvalWaitingTasks.length}
              description="Yönetici onayı bekliyor"
              icon={<FileCheck2 size={22} />}
            />

            <MetricCard
              title="Red"
              value={rejectedTasks.length}
              description="Düzeltilmesi gereken"
              icon={<XCircle size={22} />}
            />
          </div>

          <div className="grid grid-cols-1 gap-2.5">
            <ControlCheckCard
              status={openTasks.length === 0 ? "success" : "warning"}
              icon={openTasks.length === 0 ? <CheckCircle2 size={22} /> : <AlertTriangle size={22} />}
              title={openTasks.length === 0 ? "Açık görev kalmadı" : `${openTasks.length} açık görev var`}
              description={
                openTasks.length === 0
                  ? "Bekleyen, işlemde veya reddedilmiş görev görünmüyor."
                  : "Gün kapanışı öncesi bu görevler kontrol edilmeli."
              }
            />

            <ControlCheckCard
              status={approvalWaitingTasks.length === 0 ? "success" : "info"}
              icon={<FileCheck2 size={22} />}
              title={
                approvalWaitingTasks.length === 0
                  ? "Onay bekleyen görev yok"
                  : `${approvalWaitingTasks.length} görev onay bekliyor`
              }
              description={
                approvalWaitingTasks.length === 0
                  ? "Yönetici onayı bekleyen görev görünmüyor."
                  : "Onay sekmesinden bu görevler onaylanmalı veya reddedilmeli."
              }
            />

            <ControlCheckCard
              status={rejectedTasks.length === 0 ? "success" : "danger"}
              icon={rejectedTasks.length === 0 ? <CheckCircle2 size={22} /> : <XCircle size={22} />}
              title={rejectedTasks.length === 0 ? "Reddedilmiş görev yok" : `${rejectedTasks.length} görev reddedilmiş`}
              description={
                rejectedTasks.length === 0
                  ? "Düzeltme bekleyen iş görünmüyor."
                  : "Personelin düzeltip tekrar göndermesi gereken görevler var."
              }
            />

            <ControlCheckCard
              status={photoRequiredOpenTasks.length === 0 ? "success" : "warning"}
              icon={photoRequiredOpenTasks.length === 0 ? <CheckCircle2 size={22} /> : <Camera size={22} />}
              title={
                photoRequiredOpenTasks.length === 0
                  ? "Eksik fotoğraf kanıtı görünmüyor"
                  : `${photoRequiredOpenTasks.length} açık görev fotoğraf istiyor`
              }
              description={
                photoRequiredOpenTasks.length === 0
                  ? "Fotoğraf isteyen açık görev bulunmuyor."
                  : "Bu görevlerde fotoğraf kanıtı tamamlanmadan kapanış yapılmamalı."
              }
            />
          </div>

          <div className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                  Kapanış engelleri
                </p>

                <h3 className="mt-1 text-base font-black text-[var(--missio-text-main)]">
                  Günü kapatmadan önce bakılacak işler
                </h3>
              </div>

              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-200">
                <ShieldAlert size={22} />
              </div>
            </div>

            {blockingTasks.length === 0 ? (
              <div className="rounded-2xl bg-emerald-50 p-3 text-sm font-bold text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-200">
                Kontrol gerektiren açık iş görünmüyor. Gün kapatılabilir.
              </div>
            ) : (
              <div className="space-y-2">
                {blockingTasks.map((task) => (
                  <ControlTaskRow key={task.id} task={task} />
                ))}
              </div>
            )}
          </div>

          <div className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                  Personel özeti
                </p>

                <h3 className="mt-1 text-base font-black text-[var(--missio-text-main)]">
                  Kişi bazlı durum
                </h3>
              </div>

              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200">
                <UsersRound size={22} />
              </div>
            </div>

            <div className="space-y-2.5">
              {staffRows.map((row) => (
                <StaffReportCard key={row.key} row={row} />
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  )
}

export function ReportsPanel({
  tasks,
  role,
  businessId,
  onOpenTaskDetails,
}: ReportsPanelProps) {
  if (role === "staff") {
    return <StaffControlPanel tasks={tasks} onOpenTaskDetails={onOpenTaskDetails} />
  }

  return <ManagementReportPanel role={role} businessId={businessId} />
}
