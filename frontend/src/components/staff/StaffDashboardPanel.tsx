import {
  AlertCircle,
  Bell,
  ClipboardCheck,
  Clock3,
  Sparkles,
  X,
} from "lucide-react"
import { useMemo, useState, type ReactNode } from "react"
import {
  AppStatePanel,
  TaskLoadingSkeleton,
} from "../common/AppStatePanel"
import { StaffLocationCheckPanel } from "../location-checks/StaffLocationCheckPanel"
import { NotificationPanel } from "../notifications/NotificationPanel"
import { TaskCard } from "../tasks/TaskCard"
import { useTranslation } from "../../i18n/language"
import type { TodayTask } from "../../types/task"

type StaffDashboardPanelProps = {
  tasks: TodayTask[]
  isLoadingTasks: boolean
  errorMessage: string | null
  busyTaskId: number | null
  notificationCount: number
  totalCount: number
  completedCount: number
  onRefresh: () => void
  onChanged: () => void
  onOpenTaskDetails: (task: TodayTask) => void
}

type StaffSheetKind = "routine" | "extra" | "approval" | "notifications"

function isActionableTask(task: TodayTask) {
  return (
    task.status === "assigned" ||
    task.status === "in_progress" ||
    task.status === "rejected"
  )
}

function isApprovalWaitingTask(task: TodayTask) {
  return task.status === "completed" && task.requiresManagerApproval
}

function StaffBottomSheet({
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

function StaffQuickActionCard({
  title,
  icon,
  count,
  onClick,
}: {
  title: string
  icon: ReactNode
  count: number
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="relative flex min-h-[7.2rem] flex-col items-center justify-center rounded-[1.6rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 text-center shadow-sm transition active:scale-[0.98]"
    >
      {count > 0 && (
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

function StaffTaskListContent({
  title,
  emptyTitle,
  emptyDescription,
  tasks,
  isLoadingTasks,
  errorMessage,
  busyTaskId,
  onRefresh,
  onOpenTaskDetails,
}: {
  title: string
  emptyTitle: string
  emptyDescription: string
  tasks: TodayTask[]
  isLoadingTasks: boolean
  errorMessage: string | null
  busyTaskId: number | null
  onRefresh: () => void
  onOpenTaskDetails: (task: TodayTask) => void
}) {
  return (
    <section className="space-y-3">
      {isLoadingTasks && <TaskLoadingSkeleton />}

      {!isLoadingTasks && errorMessage && (
        <AppStatePanel
          icon={<AlertCircle size={30} />}
          eyebrow={title}
          title="Görevler alınamadı"
          description={errorMessage}
          tone="error"
          actionLabel="Tekrar dene"
          onAction={onRefresh}
        />
      )}

      {!isLoadingTasks && !errorMessage && tasks.length === 0 && (
        <AppStatePanel
          icon={<ClipboardCheck size={30} />}
          eyebrow={title}
          title={emptyTitle}
          description={emptyDescription}
        />
      )}

      {!isLoadingTasks &&
        !errorMessage &&
        tasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            isBusy={busyTaskId === task.id}
            onOpenDetails={onOpenTaskDetails}
          />
        ))}
    </section>
  )
}

export function StaffDashboardPanel({
  tasks,
  isLoadingTasks,
  errorMessage,
  busyTaskId,
  notificationCount,
  totalCount,
  completedCount,
  onRefresh,
  onChanged,
  onOpenTaskDetails,
}: StaffDashboardPanelProps) {
  const { language } = useTranslation()
  const isTurkish = language === "tr"
  const [activeSheet, setActiveSheet] = useState<StaffSheetKind | null>(null)

  const routineTasks = useMemo(
    () => tasks.filter((task) => task.taskType === "routine" && isActionableTask(task)),
    [tasks],
  )

  const extraTasks = useMemo(
    () => tasks.filter((task) => task.taskType === "extra" && isActionableTask(task)),
    [tasks],
  )

  const approvalWaitingTasks = useMemo(
    () => tasks.filter(isApprovalWaitingTask),
    [tasks],
  )

  const activeTaskCount = routineTasks.length + extraTasks.length

  const activeSheetTitle =
    activeSheet === "routine"
      ? isTurkish ? "Rutin Görevler" : "Routine Tasks"
      : activeSheet === "extra"
        ? isTurkish ? "Ekstra Görevler" : "Extra Tasks"
        : activeSheet === "approval"
          ? isTurkish ? "Onay Bekleyen" : "Waiting Approval"
          : isTurkish ? "Bildirimler" : "Notifications"

  return (
    <section className="flex flex-1 flex-col gap-4 pb-24">
      <section className="rounded-[2rem] bg-gradient-to-br from-slate-950 via-slate-900 to-cyan-950 p-4 text-white shadow-xl shadow-slate-950/20">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-black tracking-tight">
              {isTurkish ? "Bugünkü İş Akışı" : "Today Workflow"}
            </h1>

            <p className="mt-2 text-sm font-bold leading-6 text-slate-300">
              {isTurkish
                ? `Bugün ${activeTaskCount} aktif görevin var. ${approvalWaitingTasks.length} görev onay bekliyor.`
                : `You have ${activeTaskCount} active tasks today. ${approvalWaitingTasks.length} task is waiting for approval.`}
            </p>

            <p className="mt-2 text-xs font-bold leading-5 text-slate-400">
              {isTurkish
                ? `Toplam ${totalCount} görev · ${completedCount} tamamlanan`
                : `${totalCount} total tasks · ${completedCount} completed`}
            </p>
          </div>

          {notificationCount > 0 && (
            <span className="shrink-0 rounded-full bg-cyan-300 px-3 py-1 text-xs font-black text-slate-950">
              {notificationCount}
            </span>
          )}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="px-1 text-lg font-black text-[var(--missio-text-main)]">
          {isTurkish ? "Hızlı İşlemler" : "Quick Actions"}
        </h2>

        <div className="grid grid-cols-2 gap-3">
          <StaffQuickActionCard
            title={isTurkish ? "Rutin Görevler" : "Routine Tasks"}
            icon={<Clock3 size={24} />}
            count={routineTasks.length}
            onClick={() => setActiveSheet("routine")}
          />

          <StaffQuickActionCard
            title={isTurkish ? "Ekstra Görevler" : "Extra Tasks"}
            icon={<Sparkles size={24} />}
            count={extraTasks.length}
            onClick={() => setActiveSheet("extra")}
          />

          <StaffQuickActionCard
            title={isTurkish ? "Onay Bekleyen" : "Waiting Approval"}
            icon={<ClipboardCheck size={24} />}
            count={approvalWaitingTasks.length}
            onClick={() => setActiveSheet("approval")}
          />

          <StaffQuickActionCard
            title={isTurkish ? "Bildirimler" : "Notifications"}
            icon={<Bell size={24} />}
            count={notificationCount}
            onClick={() => setActiveSheet("notifications")}
          />
        </div>
      </section>

      <StaffBottomSheet
        isOpen={activeSheet !== null}
        title={activeSheetTitle}
        onClose={() => setActiveSheet(null)}
      >
        {activeSheet === "routine" && (
          <StaffTaskListContent
            title={isTurkish ? "Rutin Görevler" : "Routine Tasks"}
            emptyTitle={isTurkish ? "Aktif rutin görev yok" : "No active routine task"}
            emptyDescription={isTurkish ? "Yeni rutin görev atandığında burada görünecek." : "New routine tasks will appear here."}
            tasks={routineTasks}
            isLoadingTasks={isLoadingTasks}
            errorMessage={errorMessage}
            busyTaskId={busyTaskId}
            onRefresh={onRefresh}
            onOpenTaskDetails={(task) => {
              setActiveSheet(null)
              onOpenTaskDetails(task)
            }}
          />
        )}

        {activeSheet === "extra" && (
          <StaffTaskListContent
            title={isTurkish ? "Ekstra Görevler" : "Extra Tasks"}
            emptyTitle={isTurkish ? "Aktif ekstra görev yok" : "No active extra task"}
            emptyDescription={isTurkish ? "Yeni ekstra görev atandığında burada görünecek." : "New extra tasks will appear here."}
            tasks={extraTasks}
            isLoadingTasks={isLoadingTasks}
            errorMessage={errorMessage}
            busyTaskId={busyTaskId}
            onRefresh={onRefresh}
            onOpenTaskDetails={(task) => {
              setActiveSheet(null)
              onOpenTaskDetails(task)
            }}
          />
        )}

        {activeSheet === "approval" && (
          <StaffTaskListContent
            title={isTurkish ? "Onay Bekleyen" : "Waiting Approval"}
            emptyTitle={isTurkish ? "Onay bekleyen görev yok" : "No task waiting for approval"}
            emptyDescription={isTurkish ? "Tamamladığın ve onay bekleyen işler burada görünecek." : "Completed tasks waiting for approval will appear here."}
            tasks={approvalWaitingTasks}
            isLoadingTasks={isLoadingTasks}
            errorMessage={errorMessage}
            busyTaskId={busyTaskId}
            onRefresh={onRefresh}
            onOpenTaskDetails={(task) => {
              setActiveSheet(null)
              onOpenTaskDetails(task)
            }}
          />
        )}

        {activeSheet === "notifications" && (
          <div className="space-y-3">
            <StaffLocationCheckPanel onChanged={onChanged} />
            <NotificationPanel
              tasks={tasks}
              onOpenTaskDetails={(task) => {
                setActiveSheet(null)
                onOpenTaskDetails(task)
              }}
            />
          </div>
        )}
      </StaffBottomSheet>
    </section>
  )
}