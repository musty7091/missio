import {
  AlertCircle,
  CalendarClock,
  CheckCircle2,
  ClipboardCheck,
  ClipboardList,
  FileCheck2,
  ImageIcon,
  MapPin,
  Plus,
  RefreshCw,
  UserRound,
  UsersRound,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import { useTranslation, type TranslationKey } from "../../i18n/language"
import {
  listBusinessUsers,
  type BusinessUser,
} from "../../services/businessUserService"
import { listBusinessTasks } from "../../services/taskService"
import type { TaskPriority, TaskStatus, TodayTask } from "../../types/task"
import { mapApiTaskToTodayTask } from "../../utils/apiTaskMapper"
import { TaskAssignSheet } from "../tasks/TaskAssignSheet"
import { TaskCard } from "../tasks/TaskCard"

type ManagerTasksPanelProps = {
  businessId: number | null
  currentUserId: number
  busyTaskId: number | null
  onOpenOwnTaskDetails: (task: TodayTask) => void
  onChanged: () => void
}

type StaffMetrics = {
  total: number
  open: number
  done: number
  approvalPending: number
  rejected: number
}

function getLocalTodayDateKey() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, "0")
  const day = String(now.getDate()).padStart(2, "0")

  return `${year}-${month}-${day}`
}

function formatTaskTime(
  value: string | null,
  language: "tr" | "en",
  t: (key: TranslationKey) => string,
) {
  if (!value) {
    return t("manager.operations.time.none")
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return t("manager.operations.time.none")
  }

  return date.toLocaleTimeString(language === "tr" ? "tr-TR" : "en-GB", {
    hour: "2-digit",
    minute: "2-digit",
  })
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
    return parts[0].slice(0, 1).toUpperCase()
  }

  return `${parts[0].slice(0, 1)}${parts[1].slice(0, 1)}`.toUpperCase()
}

function getStatusTranslationKey(status: TaskStatus): TranslationKey {
  if (status === "assigned") return "task.status.assigned"
  if (status === "in_progress") return "task.status.inProgress"
  if (status === "completed") return "task.status.completed"
  if (status === "approved") return "task.status.approved"
  if (status === "rejected") return "task.status.rejected"
  if (status === "cancelled") return "task.status.cancelled"

  return "task.status.assigned"
}

function getPriorityTranslationKey(priority: TaskPriority): TranslationKey {
  if (priority === "urgent") return "task.priority.urgent"
  if (priority === "high") return "task.priority.high"
  if (priority === "normal") return "task.priority.normal"
  if (priority === "low") return "task.priority.low"

  return "task.priority.normal"
}

function getTaskTypeLabel(
  task: TodayTask,
  t: (key: TranslationKey) => string,
) {
  return task.taskType === "routine"
    ? t("task.type.routine")
    : t("task.type.oneTime")
}

function getStaffName(
  task: TodayTask,
  t: (key: TranslationKey) => string,
) {
  if (task.assignedToUserFullName) {
    return task.assignedToUserFullName
  }

  if (task.assignedToUsername) {
    return task.assignedToUsername
  }

  if (task.assignedToUserId) {
    return `${t("manager.operations.staff.unknownIdPrefix")} #${task.assignedToUserId}`
  }

  return t("manager.operations.staff.unknown")
}

function getReadableStatusLabel(
  task: TodayTask,
  t: (key: TranslationKey) => string,
) {
  if (task.status === "completed" && !task.requiresManagerApproval) {
    return t("task.status.completedNoApproval")
  }

  return t(getStatusTranslationKey(task.status))
}

function getStaffMetrics(tasks: TodayTask[], staffId: number): StaffMetrics {
  const staffTasks = tasks.filter((task) => task.assignedToUserId === staffId)

  return {
    total: staffTasks.length,
    open: staffTasks.filter(
      (task) =>
        task.status === "assigned" ||
        task.status === "in_progress" ||
        task.status === "rejected",
    ).length,
    done: staffTasks.filter(
      (task) =>
        task.status === "approved" ||
        (task.status === "completed" && !task.requiresManagerApproval),
    ).length,
    approvalPending: staffTasks.filter(
      (task) => task.status === "completed" && task.requiresManagerApproval,
    ).length,
    rejected: staffTasks.filter((task) => task.status === "rejected").length,
  }
}

function getTaskStatusClass(task: TodayTask) {
  if (task.status === "rejected") {
    return "rounded-full bg-red-100 px-2 py-0.5 text-[0.6rem] font-black text-red-700 dark:bg-red-950 dark:text-red-200"
  }

  if (task.status === "approved") {
    return "rounded-full bg-emerald-100 px-2 py-0.5 text-[0.6rem] font-black text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200"
  }

  if (task.status === "completed") {
    return "rounded-full bg-cyan-100 px-2 py-0.5 text-[0.6rem] font-black text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200"
  }

  if (task.status === "in_progress") {
    return "rounded-full bg-amber-100 px-2 py-0.5 text-[0.6rem] font-black text-amber-700 dark:bg-amber-950 dark:text-amber-200"
  }

  return "rounded-full bg-slate-100 px-2 py-0.5 text-[0.6rem] font-black text-slate-700 dark:bg-slate-800 dark:text-slate-200"
}

function StatTile({
  label,
  value,
  tone = "default",
}: {
  label: string
  value: number
  tone?: "default" | "warning" | "success"
}) {
  const className =
    tone === "success"
      ? "rounded-2xl bg-emerald-500/15 px-3 py-2 ring-1 ring-emerald-400/20"
      : tone === "warning"
        ? "rounded-2xl bg-amber-500/15 px-3 py-2 ring-1 ring-amber-400/20"
        : "rounded-2xl bg-white/10 px-3 py-2"

  return (
    <div className={className}>
      <p className="text-xl font-black leading-none text-white">{value}</p>
      <p className="mt-1 text-[0.64rem] font-bold text-slate-300">{label}</p>
    </div>
  )
}

function StaffCard({
  user,
  metrics,
  staffTasks,
  busyTaskId,
  onOpenTaskDetails,
}: {
  user: BusinessUser
  metrics: StaffMetrics
  staffTasks: TodayTask[]
  busyTaskId: number | null
  onOpenTaskDetails: (task: TodayTask) => void
}) {
  const { language, t } = useTranslation()
  const [isExpanded, setIsExpanded] = useState(false)
  const hasTasks = staffTasks.length > 0

  return (
    <article className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
      <button
        type="button"
        onClick={() => {
          if (hasTasks) {
            setIsExpanded((value) => !value)
          }
        }}
        className="w-full text-left"
      >
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-sm font-black text-cyan-800 dark:text-cyan-200">
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
              {metrics.total}
            </p>
            <p className="mt-1 text-[0.58rem] font-black text-[var(--missio-text-muted)]">
              {t("manager.operations.staff.task")}
            </p>
          </div>
        </div>

        <div className="mt-3 grid grid-cols-3 gap-2">
          <div className="rounded-2xl bg-[var(--missio-page-bg)] px-2 py-2 text-center">
            <p className="text-sm font-black text-[var(--missio-text-main)]">
              {metrics.open}
            </p>
            <p className="text-[0.58rem] font-black text-[var(--missio-text-muted)]">
              {t("manager.operations.staff.open")}
            </p>
          </div>

          <div className="rounded-2xl bg-[var(--missio-page-bg)] px-2 py-2 text-center">
            <p className="text-sm font-black text-[var(--missio-text-main)]">
              {metrics.approvalPending}
            </p>
            <p className="text-[0.58rem] font-black text-[var(--missio-text-muted)]">
              {t("manager.operations.staff.approval")}
            </p>
          </div>

          <div className="rounded-2xl bg-[var(--missio-page-bg)] px-2 py-2 text-center">
            <p
              className={
                metrics.rejected > 0
                  ? "text-sm font-black text-red-600 dark:text-red-300"
                  : "text-sm font-black text-[var(--missio-text-main)]"
              }
            >
              {metrics.rejected}
            </p>
            <p className="text-[0.58rem] font-black text-[var(--missio-text-muted)]">
              {t("manager.operations.staff.rejected")}
            </p>
          </div>
        </div>

        <div className="mt-3 rounded-2xl bg-[var(--missio-page-bg)] px-3 py-2 text-center text-xs font-black text-[var(--missio-text-muted)]">
          {hasTasks
            ? isExpanded
              ? t("manager.operations.staff.hideTasks")
              : t("manager.operations.staff.showTasks")
            : t("manager.operations.staff.noTasksToday")}
        </div>
      </button>

      {isExpanded && hasTasks && (
        <div className="mt-3 space-y-2 border-t border-[var(--missio-border)] pt-3">
          {staffTasks.map((task) => (
            <button
              key={task.id}
              type="button"
              onClick={() => onOpenTaskDetails(task)}
              disabled={busyTaskId === task.id}
              className="w-full rounded-[1.2rem] border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-3 text-left transition active:scale-[0.99] disabled:cursor-wait disabled:opacity-60"
            >
              <div className="mb-1.5 flex flex-wrap items-center gap-1.5">
                <span className={getTaskStatusClass(task)}>
                  {getReadableStatusLabel(task, t)}
                </span>

                <span className="rounded-full bg-violet-50 px-2 py-0.5 text-[0.6rem] font-black text-violet-700 dark:bg-violet-950 dark:text-violet-200">
                  {getTaskTypeLabel(task, t)}
                </span>

                <span className="rounded-full bg-[var(--missio-card-bg)] px-2 py-0.5 text-[0.6rem] font-black text-[var(--missio-text-muted)]">
                  {t(getPriorityTranslationKey(task.priority))}
                </span>
              </div>

              <h4 className="truncate text-sm font-black text-[var(--missio-text-main)]">
                {task.title}
              </h4>

              <div className="mt-1.5 flex flex-wrap items-center gap-2 text-[0.68rem] font-bold text-[var(--missio-text-muted)]">
                <span className="inline-flex items-center gap-1">
                  <CalendarClock size={12} />
                  {formatTaskTime(task.dueAtUtc, language, t)}
                </span>

                {task.requiresPhoto && (
                  <span className="inline-flex items-center gap-1">
                    <ImageIcon size={12} />
                    {t("task.card.photo")}
                  </span>
                )}

                {task.requiresLocation && (
                  <span className="inline-flex items-center gap-1">
                    <MapPin size={12} />
                    {t("task.card.location")}
                  </span>
                )}

                {task.requiresManagerApproval && (
                  <span className="inline-flex items-center gap-1">
                    <FileCheck2 size={12} />
                    {t("task.card.approval")}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </article>
  )
}

function ManagerTaskRow({ task }: { task: TodayTask }) {
  const { language, t } = useTranslation()
  const staffName = getStaffName(task, t)

  return (
    <article className="rounded-[1.35rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
      <div className="flex items-start gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-sm font-black text-cyan-800 dark:text-cyan-200">
          {getInitials(staffName)}
        </div>

        <div className="min-w-0 flex-1">
          <div className="mb-1.5 flex flex-wrap gap-1.5">
            <span className={getTaskStatusClass(task)}>
              {getReadableStatusLabel(task, t)}
            </span>

            <span className="rounded-full bg-violet-50 px-2 py-0.5 text-[0.6rem] font-black text-violet-700 dark:bg-violet-950 dark:text-violet-200">
              {getTaskTypeLabel(task, t)}
            </span>

            <span className="rounded-full bg-[var(--missio-page-bg)] px-2 py-0.5 text-[0.6rem] font-black text-[var(--missio-text-muted)]">
              {t(getPriorityTranslationKey(task.priority))}
            </span>
          </div>

          <h3 className="truncate text-sm font-black text-[var(--missio-text-main)]">
            {task.title}
          </h3>

          <div className="mt-1.5 flex flex-wrap items-center gap-2 text-[0.7rem] font-bold text-[var(--missio-text-muted)]">
            <span className="inline-flex items-center gap-1">
              <UserRound size={12} />
              {staffName}
            </span>

            <span className="inline-flex items-center gap-1">
              <CalendarClock size={12} />
              {formatTaskTime(task.dueAtUtc, language, t)}
            </span>

            {task.requiresPhoto && (
              <span className="inline-flex items-center gap-1">
                <ImageIcon size={12} />
                {t("task.card.photo")}
              </span>
            )}

            {task.requiresLocation && (
              <span className="inline-flex items-center gap-1">
                <MapPin size={12} />
                {t("task.card.location")}
              </span>
            )}

            {task.requiresManagerApproval && (
              <span className="inline-flex items-center gap-1">
                <FileCheck2 size={12} />
                {t("task.card.approval")}
              </span>
            )}
          </div>
        </div>
      </div>
    </article>
  )
}

export function ManagerTasksPanel({
  businessId,
  currentUserId,
  busyTaskId,
  onOpenOwnTaskDetails,
  onChanged,
}: ManagerTasksPanelProps) {
  const { t } = useTranslation()
  const [users, setUsers] = useState<BusinessUser[]>([])
  const [tasks, setTasks] = useState<TodayTask[]>([])
  const [isComposerOpen, setIsComposerOpen] = useState(false)
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
      open: tasks.filter(
        (task) =>
          task.status === "assigned" ||
          task.status === "in_progress" ||
          task.status === "rejected",
      ).length,
      approvalPending: tasks.filter(
        (task) => task.status === "completed" && task.requiresManagerApproval,
      ).length,
      done: tasks.filter(
        (task) =>
          task.status === "approved" ||
          (task.status === "completed" && !task.requiresManagerApproval),
      ).length,
    }
  }, [tasks])

  const myTasks = useMemo(
    () => tasks.filter((task) => task.assignedToUserId === currentUserId),
    [tasks, currentUserId],
  )

  const recentTasks = useMemo(
    () =>
      tasks
        .filter((task) => task.assignedToUserId !== currentUserId)
        .slice(0, 8),
    [tasks, currentUserId],
  )

  async function loadManagerData() {
    if (businessId === null) {
      setErrorMessage(t("manager.operations.error.noBusiness"))
      return
    }

    setIsLoading(true)
    setErrorMessage(null)

    try {
      const [usersResponse, tasksResponse] = await Promise.all([
        listBusinessUsers(businessId),
        listBusinessTasks({
          businessId,
          taskDate: getLocalTodayDateKey(),
          limit: 500,
          offset: 0,
        }),
      ])

      setUsers(usersResponse)
      setTasks(tasksResponse.tasks.map(mapApiTaskToTodayTask))
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage(t("manager.operations.error.loadFailed"))
      }
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadManagerData()
  }, [businessId])

  async function handleTaskCreated() {
    await loadManagerData()
    onChanged()
  }

  return (
    <section className="flex flex-1 flex-col pb-24">
      <div className="mb-4 rounded-[1.8rem] bg-slate-950 p-4 text-white shadow-xl shadow-slate-950/15">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-black text-cyan-200">
              <ClipboardCheck size={14} />
              {t("manager.operations.hero.badge")}
            </div>

            <h2 className="mt-3 text-2xl font-black leading-tight">
              {t("manager.operations.hero.title")}
            </h2>

            <p className="mt-2 text-sm font-semibold leading-5 text-slate-300">
              {t("manager.operations.hero.description")}
            </p>
          </div>

          <button
            type="button"
            onClick={() => void loadManagerData()}
            disabled={isLoading}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/10 text-cyan-200 transition active:scale-95 disabled:opacity-60"
            aria-label={t("manager.operations.refresh")}
            title={t("manager.operations.refresh")}
          >
            <RefreshCw size={19} />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <StatTile label={t("manager.operations.stat.total")} value={operationStats.total} />
          <StatTile label={t("manager.operations.stat.open")} value={operationStats.open} tone="warning" />
          <StatTile label={t("manager.operations.stat.approval")} value={operationStats.approvalPending} />
          <StatTile label={t("manager.operations.stat.done")} value={operationStats.done} tone="success" />
        </div>
      </div>

      {errorMessage && (
        <div className="mb-3 flex gap-2 rounded-[1.4rem] border border-red-200 bg-red-50 p-3 text-sm font-black text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
          <AlertCircle size={18} />
          <span>{errorMessage}</span>
        </div>
      )}

      {message && (
        <div className="mb-3 flex gap-2 rounded-[1.4rem] border border-emerald-200 bg-emerald-50 p-3 text-sm font-black text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
          <CheckCircle2 size={18} />
          <span>{message}</span>
        </div>
      )}

      <div className="mb-4 rounded-[1.7rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-black text-[var(--missio-text-main)]">
              {t("manager.operations.myTasks.title")}
            </h3>
            <p className="text-xs font-bold text-[var(--missio-text-muted)]">
              {t("manager.operations.myTasks.description")}
            </p>
          </div>

          <div className="rounded-full bg-[var(--missio-primary-soft)] px-3 py-1.5 text-xs font-black text-cyan-700 dark:text-cyan-200">
            {myTasks.length}
          </div>
        </div>

        {myTasks.length === 0 ? (
          <div className="rounded-[1.4rem] border border-dashed border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-4 text-center text-sm font-bold text-[var(--missio-text-muted)]">
            {t("manager.operations.myTasks.empty")}
          </div>
        ) : (
          <div className="space-y-2.5">
            {myTasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                isBusy={busyTaskId === task.id}
                onOpenDetails={onOpenOwnTaskDetails}
              />
            ))}
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={() => setIsComposerOpen(true)}
        className="mb-4 flex min-h-14 w-full items-center justify-center gap-2 rounded-[1.5rem] bg-[var(--missio-primary)] px-4 py-3 text-sm font-black text-white shadow-lg shadow-teal-500/20 transition active:scale-95"
      >
        <Plus size={20} />
        {t("manager.operations.assignNew")}
      </button>

      <div className="mb-4">
        <div className="mb-2 flex items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-black text-[var(--missio-text-main)]">
              {t("manager.operations.staff.title")}
            </h3>
            <p className="text-xs font-bold text-[var(--missio-text-muted)]">
              {t("manager.operations.staff.description")}
            </p>
          </div>

          <div className="inline-flex items-center gap-1.5 rounded-full bg-[var(--missio-primary-soft)] px-3 py-1.5 text-xs font-black text-cyan-700 dark:text-cyan-200">
            <UsersRound size={14} />
            {staffUsers.length}
          </div>
        </div>

        {staffUsers.length === 0 ? (
          <div className="rounded-[1.6rem] border border-dashed border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-5 text-center text-sm font-bold text-[var(--missio-text-muted)]">
            {t("manager.operations.staff.empty")}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-2.5">
            {staffUsers.map((user) => {
              const staffTasks = tasks.filter(
                (task) => task.assignedToUserId === user.id,
              )

              return (
                <StaffCard
                  key={user.id}
                  user={user}
                  metrics={getStaffMetrics(tasks, user.id)}
                  staffTasks={staffTasks}
                  busyTaskId={busyTaskId}
                  onOpenTaskDetails={onOpenOwnTaskDetails}
                />
              )
            })}
          </div>
        )}
      </div>

      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-black text-[var(--missio-text-main)]">
            {t("manager.operations.recent.title")}
          </h3>
          <p className="text-xs font-bold text-[var(--missio-text-muted)]">
            {t("manager.operations.recent.description")}
          </p>
        </div>

        <div className="rounded-full bg-[var(--missio-page-bg)] px-3 py-1.5 text-xs font-black text-[var(--missio-text-muted)]">
          {tasks.length}
        </div>
      </div>

      {isLoading ? (
        <div className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 text-sm font-black text-[var(--missio-text-muted)]">
          {t("manager.operations.loading")}
        </div>
      ) : tasks.length === 0 ? (
        <div className="rounded-[1.7rem] border border-dashed border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-6 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-3xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
            <ClipboardList size={28} />
          </div>

          <h3 className="mt-4 text-lg font-black">{t("manager.operations.empty.title")}</h3>

          <p className="mt-2 text-sm font-semibold leading-6 text-[var(--missio-text-muted)]">
            {t("manager.operations.empty.description")}
          </p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {recentTasks.map((task) => (
            <ManagerTaskRow key={task.id} task={task} />
          ))}
        </div>
      )}

      <TaskAssignSheet
        businessId={businessId}
        isOpen={isComposerOpen}
        assignableRoles={["staff"]}
        defaultRequiresManagerApproval
        allowLocationRequirement
        onClose={() => setIsComposerOpen(false)}
        onCreated={handleTaskCreated}
        onSuccess={setMessage}
      />
    </section>
  )
}
