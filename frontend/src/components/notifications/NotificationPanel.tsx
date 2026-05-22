import {
  Bell,
  Camera,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock3,
  FileCheck2,
  Info,
  PlayCircle,
  Sparkles,
} from "lucide-react"
import { useState } from "react"
import type { TodayTask } from "../../types/task"
import { getPriorityLabel, getStatusLabel } from "../../utils/taskLabels"

type NotificationPanelProps = {
  tasks: TodayTask[]
  onOpenTaskDetails: (task: TodayTask) => void
}

type NotificationTone = "warning" | "info" | "success" | "extra"

type NotificationItem = {
  id: string
  title: string
  message: string
  timeLabel: string
  meta: string
  tone: NotificationTone
  icon: typeof Bell
  isUnread: boolean
  relatedTasks: TodayTask[]
}

function getToneStyles(tone: NotificationTone) {
  const styles = {
    warning: {
      icon: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-200",
      badge: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-200",
      dot: "bg-amber-500",
      line: "bg-amber-400",
    },
    info: {
      icon: "bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200",
      badge: "bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200",
      dot: "bg-cyan-500",
      line: "bg-cyan-400",
    },
    success: {
      icon: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200",
      badge: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200",
      dot: "bg-emerald-500",
      line: "bg-emerald-400",
    },
    extra: {
      icon: "bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-200",
      badge: "bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-200",
      dot: "bg-violet-500",
      line: "bg-violet-400",
    },
  }

  return styles[tone]
}

function formatNotificationTime(value: string | null) {
  if (!value) {
    return "Saat yok"
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return "Saat yok"
  }

  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()

  const time = date.toLocaleTimeString("tr-TR", {
    hour: "2-digit",
    minute: "2-digit",
  })

  if (isToday) {
    return `Bugün ${time}`
  }

  return (
    date.toLocaleDateString("tr-TR", {
      day: "2-digit",
      month: "2-digit",
    }) + ` ${time}`
  )
}

function getLatestTime(tasks: TodayTask[], field: keyof TodayTask) {
  const dates = tasks
    .map((task) => task[field])
    .filter((value): value is string => typeof value === "string" && value.length > 0)
    .map((value) => new Date(value))
    .filter((date) => !Number.isNaN(date.getTime()))
    .sort((a, b) => b.getTime() - a.getTime())

  return dates[0]?.toISOString() ?? null
}

function getTaskPreview(tasks: TodayTask[]) {
  if (tasks.length === 0) {
    return ""
  }

  if (tasks.length === 1) {
    return tasks[0].title
  }

  return `${tasks[0].title} ve ${tasks.length - 1} görev daha`
}

function buildAssignmentNotifications(tasks: TodayTask[]) {
  const notifications: NotificationItem[] = []

  const routineTasks = tasks.filter((task) => task.taskType === "routine")
  const extraTasks = tasks.filter((task) => task.taskType === "extra")

  if (routineTasks.length > 0) {
    notifications.push({
      id: "routine-assigned",
      title: `${routineTasks.length} rutin görev atandı`,
      message: `Günlük rutin görevlerin hazır. İlk görev: ${getTaskPreview(routineTasks)}.`,
      timeLabel: formatNotificationTime(getLatestTime(routineTasks, "assignedAtUtc")),
      meta: "Rutin görev",
      tone: "info",
      icon: Clock3,
      isUnread: routineTasks.some((task) => task.status === "assigned"),
      relatedTasks: routineTasks,
    })
  }

  if (extraTasks.length > 0) {
    notifications.push({
      id: "extra-assigned",
      title: `${extraTasks.length} ekstra görev atandı`,
      message: `Bugüne özel ekstra görevlerin var. İlk görev: ${getTaskPreview(extraTasks)}.`,
      timeLabel: formatNotificationTime(getLatestTime(extraTasks, "assignedAtUtc")),
      meta: "Ekstra görev",
      tone: "extra",
      icon: Sparkles,
      isUnread: extraTasks.some((task) => task.status === "assigned"),
      relatedTasks: extraTasks,
    })
  }

  return notifications
}

function buildAttentionNotifications(tasks: TodayTask[]) {
  const notifications: NotificationItem[] = []

  const activeTasks = tasks.filter((task) => task.status === "in_progress")
  const photoRequiredTasks = tasks.filter(
    (task) =>
      task.requiresPhoto &&
      task.status !== "completed" &&
      task.status !== "approved" &&
      task.status !== "cancelled",
  )
  const approvalWaitingTasks = tasks.filter(
    (task) => task.status === "completed" && task.requiresManagerApproval,
  )
  const completedTasks = tasks.filter(
    (task) => task.status === "completed" || task.status === "approved",
  )

  if (activeTasks.length > 0) {
    notifications.push({
      id: "active-tasks",
      title: "Devam eden görev var",
      message: `${getTaskPreview(activeTasks)} şu anda işlemde. İş bittiyse tamamlandı olarak işaretlenmeli.`,
      timeLabel: formatNotificationTime(getLatestTime(activeTasks, "startedAtUtc")),
      meta: "Aksiyon gerekli",
      tone: "warning",
      icon: PlayCircle,
      isUnread: true,
      relatedTasks: activeTasks,
    })
  }

  if (photoRequiredTasks.length > 0) {
    notifications.push({
      id: "photo-required",
      title: "Kanıtlı görev var",
      message: `${photoRequiredTasks.length} görev fotoğraf kanıtı istiyor. Kanıt eklenmeden görev tamamlanamayabilir.`,
      timeLabel: "Kanıt gerekli",
      meta: "Dikkat",
      tone: "warning",
      icon: Camera,
      isUnread: true,
      relatedTasks: photoRequiredTasks,
    })
  }

  if (approvalWaitingTasks.length > 0) {
    notifications.push({
      id: "approval-waiting",
      title: "Onay bekleyen görev var",
      message: `${approvalWaitingTasks.length} tamamlanan görev yönetici onayı bekliyor.`,
      timeLabel: formatNotificationTime(getLatestTime(approvalWaitingTasks, "completedAtUtc")),
      meta: "Onay süreci",
      tone: "info",
      icon: FileCheck2,
      isUnread: false,
      relatedTasks: approvalWaitingTasks,
    })
  }

  if (completedTasks.length > 0) {
    notifications.push({
      id: "completed-tasks",
      title: "Tamamlanan görev bildirimi",
      message: `Bugün ${completedTasks.length} görev tamamlandı veya onaylandı.`,
      timeLabel: formatNotificationTime(getLatestTime(completedTasks, "completedAtUtc")),
      meta: "Bilgi",
      tone: "success",
      icon: CheckCircle2,
      isUnread: false,
      relatedTasks: completedTasks,
    })
  }

  return notifications
}

function NotificationTaskRow({
  task,
  onOpenTaskDetails,
}: {
  task: TodayTask
  onOpenTaskDetails: (task: TodayTask) => void
}) {
  return (
    <button
      type="button"
      onClick={() => onOpenTaskDetails(task)}
      className="flex w-full items-center justify-between gap-3 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-3 py-2.5 text-left active:scale-[0.99]"
    >
      <div className="min-w-0">
        <div className="mb-1 flex flex-wrap gap-1.5">
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
        </div>

        <p className="truncate text-sm font-black text-[var(--missio-text-main)]">
          {task.title}
        </p>

        <p className="mt-1 truncate text-[0.68rem] font-bold text-[var(--missio-text-muted)]">
          Atanma: {formatNotificationTime(task.assignedAtUtc)}
        </p>
      </div>

      <ChevronRight className="shrink-0 text-[var(--missio-text-muted)]" size={18} />
    </button>
  )
}

function NotificationCard({
  notification,
  isExpanded,
  onToggle,
  onOpenTaskDetails,
}: {
  notification: NotificationItem
  isExpanded: boolean
  onToggle: () => void
  onOpenTaskDetails: (task: TodayTask) => void
}) {
  const Icon = notification.icon
  const toneStyles = getToneStyles(notification.tone)
  const hasRelatedTasks = notification.relatedTasks.length > 0

  return (
    <article className="relative overflow-hidden rounded-[1.4rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] shadow-sm">
      <button
        type="button"
        onClick={onToggle}
        className="relative w-full p-3 text-left active:scale-[0.995]"
      >
        {notification.isUnread && (
          <span
            className={`absolute right-3 top-3 h-2.5 w-2.5 rounded-full ${toneStyles.dot}`}
          />
        )}

        <div className="flex items-start gap-3 pr-4">
          <div
            className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl ${toneStyles.icon}`}
          >
            <Icon size={20} />
          </div>

          <div className="min-w-0 flex-1">
            <div className="mb-1.5 flex flex-wrap items-center gap-2">
              <span
                className={`rounded-full px-2.5 py-1 text-[0.62rem] font-black ${toneStyles.badge}`}
              >
                {notification.meta}
              </span>

              <span className="rounded-full bg-[var(--missio-page-bg)] px-2.5 py-1 text-[0.62rem] font-black text-[var(--missio-text-muted)]">
                {notification.timeLabel}
              </span>
            </div>

            <h3 className="text-sm font-black text-[var(--missio-text-main)]">
              {notification.title}
            </h3>

            <p className="mt-1 text-xs font-bold leading-5 text-[var(--missio-text-muted)]">
              {notification.message}
            </p>

            {hasRelatedTasks && (
              <div className="mt-2 flex items-center gap-1.5 text-xs font-black text-[var(--missio-text-muted)]">
                {isExpanded ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
                <span>
                  {isExpanded
                    ? "Görevleri gizle"
                    : `${notification.relatedTasks.length} görevi göster`}
                </span>
              </div>
            )}
          </div>
        </div>
      </button>

      {isExpanded && hasRelatedTasks && (
        <div className="space-y-2 border-t border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-3 pb-3 pt-2">
          <div className={`h-1 rounded-full ${toneStyles.line}`} />

          {notification.relatedTasks.map((task) => (
            <NotificationTaskRow
              key={task.id}
              task={task}
              onOpenTaskDetails={onOpenTaskDetails}
            />
          ))}
        </div>
      )}
    </article>
  )
}

export function NotificationPanel({
  tasks,
  onOpenTaskDetails,
}: NotificationPanelProps) {
  const [expandedNotificationId, setExpandedNotificationId] = useState<string | null>(null)

  const assignmentNotifications = buildAssignmentNotifications(tasks)
  const attentionNotifications = buildAttentionNotifications(tasks)
  const notifications = [...assignmentNotifications, ...attentionNotifications]

  function toggleNotification(notificationId: string) {
    setExpandedNotificationId((currentId) =>
      currentId === notificationId ? null : notificationId,
    )
  }

  return (
    <section className="flex flex-1 flex-col pb-24">
      <div className="mb-4 rounded-[1.7rem] bg-slate-950 p-4 text-white shadow-xl shadow-slate-950/15">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-black text-cyan-200">
              <Bell size={14} />
              Bildirimler
            </div>

            <h2 className="mt-3 text-2xl font-black leading-tight">
              Bugünkü bildirimler
            </h2>

            <p className="mt-2 text-sm font-semibold leading-5 text-slate-300">
              Bildirime dokunarak ilgili görevleri görüntüleyebilirsin.
            </p>
          </div>
        </div>
      </div>

      {notifications.length === 0 ? (
        <div className="flex flex-1 items-center justify-center rounded-[1.7rem] border border-dashed border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-6 text-center">
          <div>
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-3xl bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200">
              <CheckCircle2 size={28} />
            </div>

            <h3 className="mt-4 text-lg font-black">Yeni bildirim yok</h3>

            <p className="mt-2 text-sm font-semibold leading-6 text-[var(--missio-text-muted)]">
              Şu anda dikkat gerektiren görev bildirimi bulunmuyor.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {assignmentNotifications.length > 0 && (
            <div className="space-y-2.5">
              <div className="flex items-center justify-between px-1">
                <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                  Görev atamaları
                </p>

                <span className="rounded-full bg-[var(--missio-card-bg)] px-2.5 py-1 text-[0.65rem] font-black text-[var(--missio-text-muted)]">
                  {assignmentNotifications.length} kayıt
                </span>
              </div>

              {assignmentNotifications.map((notification) => (
                <NotificationCard
                  key={notification.id}
                  notification={notification}
                  isExpanded={expandedNotificationId === notification.id}
                  onToggle={() => toggleNotification(notification.id)}
                  onOpenTaskDetails={onOpenTaskDetails}
                />
              ))}
            </div>
          )}

          {attentionNotifications.length > 0 && (
            <div className="space-y-2.5">
              <div className="flex items-center justify-between px-1">
                <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                  Dikkat edilmesi gerekenler
                </p>

                <span className="rounded-full bg-[var(--missio-card-bg)] px-2.5 py-1 text-[0.65rem] font-black text-[var(--missio-text-muted)]">
                  {attentionNotifications.length} kayıt
                </span>
              </div>

              {attentionNotifications.map((notification) => (
                <NotificationCard
                  key={notification.id}
                  notification={notification}
                  isExpanded={expandedNotificationId === notification.id}
                  onToggle={() => toggleNotification(notification.id)}
                  onOpenTaskDetails={onOpenTaskDetails}
                />
              ))}
            </div>
          )}

          <div className="rounded-[1.4rem] border border-dashed border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3">
            <div className="flex items-start gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                <Info size={20} />
              </div>

              <div>
                <h3 className="text-sm font-black text-[var(--missio-text-main)]">
                  Bildirimden göreve hızlı geçiş
                </h3>

                <p className="mt-1 text-xs font-bold leading-5 text-[var(--missio-text-muted)]">
                  Bildirime dokun, ilgili görevleri gör, görev satırına dokunarak detayına geç.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}


