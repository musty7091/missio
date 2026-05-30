import {
  AlertCircle,
  BarChart3,
  CheckCircle2,
  ClipboardCheck,
  ClipboardList,
  MapPin,
  PlusSquare,
  RefreshCw,
  UsersRound,
  X,
} from "lucide-react"
import { useEffect, useMemo, useState, type ReactNode } from "react"
import { useTranslation } from "../../i18n/language"
import {
  listBusinessUsers,
  type BusinessUser,
} from "../../services/businessUserService"
import { listBusinessTasks } from "../../services/taskService"
import type { TodayTask } from "../../types/task"
import { mapApiTaskToTodayTask } from "../../utils/apiTaskMapper"
import { LocationCheckRequestPanel } from "../location-checks/LocationCheckRequestPanel"
import { StaffLocationCheckPanel } from "../location-checks/StaffLocationCheckPanel"
import { TaskAssignSheet } from "../tasks/TaskAssignSheet"
import { TaskCard } from "../tasks/TaskCard"

type ManagerTasksPanelProps = {
  businessId: number | null
  currentUserId: number
  busyTaskId: number | null
  onOpenOwnTaskDetails: (task: TodayTask) => void
  onOpenApprovals?: () => void
  onOpenReports?: () => void
  onChanged: () => void
}

type ManagerSheetKind = "assign" | "location" | "staff" | "tasks"

function getLocalTodayDateKey() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, "0")
  const day = String(now.getDate()).padStart(2, "0")

  return `${year}-${month}-${day}`
}

function isOpenTask(task: TodayTask) {
  return (
    task.status === "assigned" ||
    task.status === "in_progress" ||
    task.status === "rejected"
  )
}

function isApprovalWaitingTask(task: TodayTask) {
  return task.status === "completed" && task.requiresManagerApproval
}

function isDoneTask(task: TodayTask) {
  return (
    task.status === "approved" ||
    (task.status === "completed" && !task.requiresManagerApproval)
  )
}

function getInitials(name: string) {
  const parts = name
    .split(" ")
    .map((part) => part.trim())
    .filter(Boolean)

  if (parts.length === 0) {
    return "P"
  }

  if (parts.length === 1) {
    return parts[0].slice(0, 2).toLocaleUpperCase("tr-TR")
  }

  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toLocaleUpperCase("tr-TR")
}

function ManagerBottomSheet({
  isOpen,
  title,
  onClose,
  children,
}: {
  isOpen: boolean
  title: string
  onClose: () => void
  children: ReactNode
}) {
  if (!isOpen) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/55 px-3 pb-3 pt-16 backdrop-blur-sm">
      <div className="max-h-[88vh] w-full max-w-md overflow-hidden rounded-[2rem] bg-[var(--missio-page-bg)] shadow-2xl">
        <div className="flex items-center justify-between gap-3 border-b border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-3">
          <h2 className="text-base font-black text-[var(--missio-text-main)]">
            {title}
          </h2>

          <button
            type="button"
            onClick={onClose}
            className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[var(--missio-page-bg)] text-[var(--missio-text-main)] transition active:scale-95"
            aria-label="Kapat"
          >
            <X size={20} />
          </button>
        </div>

        <div className="max-h-[calc(88vh-4rem)] overflow-y-auto p-3">
          {children}
        </div>
      </div>
    </div>
  )
}

function SummaryMiniCard({
  label,
  value,
}: {
  label: string
  value: string | number
}) {
  return (
    <div className="rounded-2xl bg-white/10 px-3 py-3">
      <p className="text-2xl font-black text-white">{value}</p>
      <p className="mt-1 text-[0.68rem] font-bold leading-4 text-slate-300">
        {label}
      </p>
    </div>
  )
}

function ManagerQuickActionCard({
  title,
  icon,
  onClick,
  count,
}: {
  title: string
  icon: ReactNode
  onClick: () => void
  count?: number | null
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="relative flex min-h-[7.2rem] flex-col items-center justify-center rounded-[1.6rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 text-center shadow-sm transition active:scale-[0.98]"
    >
      {count !== null && count !== undefined && count > 0 && (
        <span className="absolute right-3 top-3 min-w-6 rounded-full bg-[var(--missio-primary)] px-2 py-1 text-xs font-black text-white">
          {count}
        </span>
      )}

      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-50 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200">
        {icon}
      </div>

      <span className="text-sm font-black text-[var(--missio-text-main)]">
        {title}
      </span>
    </button>
  )
}

function StaffSummaryCard({
  user,
  tasks,
}: {
  user: BusinessUser
  tasks: TodayTask[]
}) {
  const openCount = tasks.filter(isOpenTask).length
  const approvalCount = tasks.filter(isApprovalWaitingTask).length
  const doneCount = tasks.filter(isDoneTask).length

  return (
    <article className="rounded-[1.35rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-sm font-black text-cyan-800 dark:text-cyan-200">
          {getInitials(user.full_name)}
        </div>

        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-black text-[var(--missio-text-main)]">
            {user.full_name}
          </h3>
          <p className="mt-0.5 truncate text-xs font-bold text-[var(--missio-text-muted)]">
            @{user.username}
          </p>
        </div>

        <div className="rounded-2xl bg-[var(--missio-page-bg)] px-3 py-2 text-center">
          <p className="text-base font-black leading-none text-[var(--missio-text-main)]">
            {tasks.length}
          </p>
          <p className="mt-1 text-[0.58rem] font-black text-[var(--missio-text-muted)]">
            görev
          </p>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-3 gap-2 text-center">
        <div className="rounded-2xl bg-[var(--missio-page-bg)] px-2 py-2">
          <p className="text-sm font-black text-amber-600">{openCount}</p>
          <p className="text-[0.58rem] font-black text-[var(--missio-text-muted)]">
            açık
          </p>
        </div>

        <div className="rounded-2xl bg-[var(--missio-page-bg)] px-2 py-2">
          <p className="text-sm font-black text-cyan-600">{approvalCount}</p>
          <p className="text-[0.58rem] font-black text-[var(--missio-text-muted)]">
            onay
          </p>
        </div>

        <div className="rounded-2xl bg-[var(--missio-page-bg)] px-2 py-2">
          <p className="text-sm font-black text-emerald-600">{doneCount}</p>
          <p className="text-[0.58rem] font-black text-[var(--missio-text-muted)]">
            tamam
          </p>
        </div>
      </div>
    </article>
  )
}

function TaskListSheetContent({
  tasks,
  busyTaskId,
  onOpenTaskDetails,
  emptyText,
}: {
  tasks: TodayTask[]
  busyTaskId: number | null
  onOpenTaskDetails: (task: TodayTask) => void
  emptyText: string
}) {
  if (tasks.length === 0) {
    return (
      <div className="rounded-[1.5rem] border border-dashed border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-6 text-center text-sm font-bold text-[var(--missio-text-muted)]">
        {emptyText}
      </div>
    )
  }

  return (
    <div className="space-y-2.5">
      {tasks.map((task) => (
        <TaskCard
          key={task.id}
          task={task}
          isBusy={busyTaskId === task.id}
          onOpenDetails={onOpenTaskDetails}
        />
      ))}
    </div>
  )
}

export function ManagerTasksPanel({
  businessId,
  currentUserId,
  busyTaskId,
  onOpenOwnTaskDetails,
  onOpenApprovals = () => undefined,
  onOpenReports = () => undefined,
  onChanged,
}: ManagerTasksPanelProps) {
  const { language } = useTranslation()
  const isTurkish = language === "tr"
  const todayKey = getLocalTodayDateKey()

  const [users, setUsers] = useState<BusinessUser[]>([])
  const [tasks, setTasks] = useState<TodayTask[]>([])
  const [activeSheet, setActiveSheet] = useState<ManagerSheetKind | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const staffUsers = useMemo(
    () => users.filter((user) => user.role === "staff" && user.is_active),
    [users],
  )

  const operationStats = useMemo(() => {
    return {
      total: tasks.length,
      open: tasks.filter(isOpenTask).length,
      approvalPending: tasks.filter(isApprovalWaitingTask).length,
      done: tasks.filter(isDoneTask).length,
    }
  }, [tasks])

  const myTasks = useMemo(
    () => tasks.filter((task) => task.assignedToUserId === currentUserId),
    [tasks, currentUserId],
  )
async function loadManagerData(options: { showLoading?: boolean } = {}) {
    const showLoading = options.showLoading ?? true

    if (businessId === null) {
      setErrorMessage(isTurkish ? "İşletme bilgisi bulunamadı." : "Business information could not be found.")
      return
    }

    if (showLoading) {
      setIsLoading(true)
    }

    try {
      const [userResponse, taskResponse] = await Promise.all([
        listBusinessUsers(businessId),
        listBusinessTasks({
          businessId,
          taskDate: todayKey,
          limit: 500,
          offset: 0,
        }),
      ])

      setUsers(userResponse)
      setTasks(taskResponse.tasks.map(mapApiTaskToTodayTask))
      setErrorMessage(null)
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage(isTurkish ? "Yönetici ekranı yüklenemedi." : "Manager screen could not be loaded.")
      }
    } finally {
      if (showLoading) {
        setIsLoading(false)
      }
    }
  }

  useEffect(() => {
    void loadManagerData()
  }, [businessId])

  useEffect(() => {
    if (businessId === null) {
      return
    }

    function refreshManagerDataWhenVisible() {
      if (document.visibilityState === "visible") {
        void loadManagerData({ showLoading: false })
      }
    }

    const intervalId = window.setInterval(refreshManagerDataWhenVisible, 10000)

    window.addEventListener("focus", refreshManagerDataWhenVisible)
    document.addEventListener("visibilitychange", refreshManagerDataWhenVisible)

    return () => {
      window.clearInterval(intervalId)
      window.removeEventListener("focus", refreshManagerDataWhenVisible)
      document.removeEventListener("visibilitychange", refreshManagerDataWhenVisible)
    }
  }, [businessId, todayKey])

  async function handleTaskCreated() {
    await loadManagerData()
    onChanged()
  }

  function handleLocationCheckChanged() {
    void loadManagerData({ showLoading: false })
    onChanged()
  }

  const sheetTitle =
    activeSheet === "assign"
      ? isTurkish ? "Görev Ata" : "Assign Task"
      : activeSheet === "location"
        ? isTurkish ? "Konum İste" : "Request Location"
        : activeSheet === "staff"
          ? isTurkish ? "Personel" : "Personnel"
          : isTurkish ? "Görevlerim" : "My Tasks"

  return (
    <section className="flex flex-1 flex-col gap-4 pb-24">
      <section className="rounded-[2rem] bg-gradient-to-br from-slate-950 via-slate-900 to-cyan-950 p-4 text-white shadow-xl shadow-slate-950/20">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-black tracking-tight">
              {isTurkish ? "Ekip Özeti" : "Team Summary"}
            </h1>

            <p className="mt-2 max-w-sm text-sm font-bold leading-6 text-slate-300">
              {isTurkish
                ? "Ekip görevlerini, onayları ve günlük akışı hızlıca takip et."
                : "Track team tasks, approvals and daily flow quickly."}
            </p>
          </div>

          <button
            type="button"
            onClick={() => void loadManagerData()}
            disabled={isLoading}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/10 text-cyan-100 transition active:scale-95 disabled:opacity-60"
            aria-label={isTurkish ? "Yenile" : "Refresh"}
          >
            <RefreshCw className={isLoading ? "animate-spin" : ""} size={19} />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <SummaryMiniCard
            label={isTurkish ? "Ekip görevi" : "Team tasks"}
            value={operationStats.total}
          />

          <SummaryMiniCard
            label={isTurkish ? "Açık görev" : "Open tasks"}
            value={operationStats.open}
          />

          <SummaryMiniCard
            label={isTurkish ? "Onay bekleyen" : "Waiting approval"}
            value={operationStats.approvalPending}
          />

          <SummaryMiniCard
            label={isTurkish ? "Tamamlanan" : "Completed"}
            value={operationStats.done}
          />
        </div>
      </section>

      {errorMessage && (
        <div className="flex gap-2 rounded-[1.4rem] border border-red-200 bg-red-50 p-3 text-sm font-black text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
          <AlertCircle size={18} />
          <span>{errorMessage}</span>
        </div>
      )}

      {message && (
        <div className="flex gap-2 rounded-[1.4rem] border border-emerald-200 bg-emerald-50 p-3 text-sm font-black text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
          <CheckCircle2 size={18} />
          <span>{message}</span>
        </div>
      )}

      <StaffLocationCheckPanel
        silentLoading
        onChanged={handleLocationCheckChanged}
      />

      <section className="space-y-3">
        <h2 className="px-1 text-lg font-black text-[var(--missio-text-main)]">
          {isTurkish ? "Hızlı İşlemler" : "Quick Actions"}
        </h2>

        <div className="grid grid-cols-2 gap-3">
          <ManagerQuickActionCard
            title={isTurkish ? "Görev Ata" : "Assign Task"}
            icon={<PlusSquare size={24} />}
            onClick={() => setActiveSheet("assign")}
          />

          <ManagerQuickActionCard
            title={isTurkish ? "Konum İste" : "Request Location"}
            icon={<MapPin size={24} />}
            onClick={() => setActiveSheet("location")}
          />

          <ManagerQuickActionCard
            title={isTurkish ? "Onaylar" : "Approvals"}
            icon={<ClipboardCheck size={24} />}
            count={operationStats.approvalPending}
            onClick={onOpenApprovals}
          />

          <ManagerQuickActionCard
            title={isTurkish ? "Raporlar" : "Reports"}
            icon={<BarChart3 size={24} />}
            onClick={onOpenReports}
          />

          <ManagerQuickActionCard
            title={isTurkish ? "Personel" : "Personnel"}
            icon={<UsersRound size={24} />}
            count={staffUsers.length}
            onClick={() => setActiveSheet("staff")}
          />

          <ManagerQuickActionCard
            title={isTurkish ? "Görevlerim" : "My Tasks"}
            icon={<ClipboardList size={24} />}
            count={myTasks.length}
            onClick={() => setActiveSheet("tasks")}
          />
        </div>
      </section>

      <ManagerBottomSheet
        isOpen={activeSheet !== null}
        title={sheetTitle}
        onClose={() => setActiveSheet(null)}
      >
        {activeSheet === "assign" && (
          <TaskAssignSheet
            businessId={businessId}
            isOpen
            assignableRoles={["staff"]}
            defaultRequiresManagerApproval
            allowLocationRequirement
            onClose={() => setActiveSheet(null)}
            onCreated={handleTaskCreated}
            onSuccess={setMessage}
          />
        )}

        {activeSheet === "location" && (
          <LocationCheckRequestPanel
            businessId={businessId}
            allowedTargetRoles={["staff"]}
          />
        )}

        {activeSheet === "staff" && (
          <div className="space-y-2.5">
            {staffUsers.length === 0 ? (
              <div className="rounded-[1.5rem] border border-dashed border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-6 text-center text-sm font-bold text-[var(--missio-text-muted)]">
                {isTurkish ? "Aktif personel görünmüyor." : "No active staff found."}
              </div>
            ) : (
              staffUsers.map((user) => (
                <StaffSummaryCard
                  key={user.id}
                  user={user}
                  tasks={tasks.filter((task) => task.assignedToUserId === user.id)}
                />
              ))
            )}
          </div>
        )}

        {activeSheet === "tasks" && (
          <TaskListSheetContent
            tasks={myTasks}
            busyTaskId={busyTaskId}
            onOpenTaskDetails={(task) => {
              setActiveSheet(null)
              onOpenOwnTaskDetails(task)
            }}
            emptyText={isTurkish ? "Bugün sana atanmış görev yok." : "No task assigned to you today."}
          />
        )}
      </ManagerBottomSheet>
    </section>
  )
}