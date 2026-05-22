import {
  Camera,
  CheckCircle2,
  ChevronRight,
  Clock3,
  FileCheck2,
  MapPin,
  PlayCircle,
  XCircle,
} from "lucide-react"
import type { TodayTask } from "../../types/task"
import { getPriorityLabel, getStatusLabel } from "../../utils/taskLabels"

type TaskCardProps = {
  task: TodayTask
  isBusy: boolean
  onOpenDetails: (task: TodayTask) => void
}

function getStatusIcon(task: TodayTask) {
  if (task.status === "rejected") {
    return <XCircle size={20} />
  }

  if (task.status === "completed" || task.status === "approved") {
    return <CheckCircle2 size={20} />
  }

  if (task.status === "in_progress") {
    return <PlayCircle size={20} />
  }

  return <Clock3 size={20} />
}

function getCardClass(task: TodayTask) {
  if (task.status === "rejected") {
    return "w-full rounded-[1.35rem] border border-red-200 bg-red-50/80 p-3 text-left shadow-sm transition active:scale-[0.99] disabled:cursor-wait disabled:opacity-70 dark:border-red-900 dark:bg-red-950/25"
  }

  return "w-full rounded-[1.35rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 text-left shadow-sm transition active:scale-[0.99] disabled:cursor-wait disabled:opacity-70"
}

function getIconBoxClass(task: TodayTask) {
  if (task.status === "rejected") {
    return "flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-200"
  }

  if (task.status === "approved" || task.status === "completed") {
    return "flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200"
  }

  return "flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200"
}

function getStatusBadgeClass(task: TodayTask) {
  if (task.status === "rejected") {
    return "rounded-full bg-red-100 px-2.5 py-1 text-[0.65rem] font-black text-red-700 dark:bg-red-950 dark:text-red-200"
  }

  if (task.status === "approved") {
    return "rounded-full bg-emerald-100 px-2.5 py-1 text-[0.65rem] font-black text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200"
  }

  if (task.status === "completed") {
    return "rounded-full bg-cyan-100 px-2.5 py-1 text-[0.65rem] font-black text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200"
  }

  return "rounded-full bg-[var(--missio-primary-soft)] px-2.5 py-1 text-[0.65rem] font-black text-cyan-700 dark:text-cyan-200"
}

function getTaskCardStatusLabel(task: TodayTask) {
  if (task.status === "completed" && !task.requiresManagerApproval) {
    return "Tamamlandı"
  }

  return getStatusLabel(task.status)
}

export function TaskCard({ task, isBusy, onOpenDetails }: TaskCardProps) {
  return (
    <button
      type="button"
      onClick={() => onOpenDetails(task)}
      disabled={isBusy}
      className={getCardClass(task)}
    >
      <div className="flex items-center gap-3">
        <div className={getIconBoxClass(task)}>
          {getStatusIcon(task)}
        </div>

        <div className="min-w-0 flex-1">
          <div className="mb-1 flex flex-wrap items-center gap-1.5">
            <span className={getStatusBadgeClass(task)}>
              {getTaskCardStatusLabel(task)}
            </span>

            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[0.65rem] font-black text-slate-700 dark:bg-slate-800 dark:text-slate-200">
              {task.taskType === "routine" ? "Rutin" : "Ekstra"}
            </span>

            {task.priority !== "normal" && (
              <span className="rounded-full bg-amber-50 px-2.5 py-1 text-[0.65rem] font-black text-amber-700 dark:bg-amber-950 dark:text-amber-200">
                {getPriorityLabel(task.priority)}
              </span>
            )}
          </div>

          <h3 className="truncate text-sm font-black text-[var(--missio-text-main)]">
            {task.title}
          </h3>

          <div className="mt-1 flex flex-wrap items-center gap-2 text-[0.7rem] font-bold text-[var(--missio-text-muted)]">
            <span className="inline-flex items-center gap-1">
              <Clock3 size={12} />
              {task.time}
            </span>

            {task.status === "rejected" && (
              <span className="inline-flex items-center gap-1 font-black text-red-700 dark:text-red-200">
                <XCircle size={12} />
                Tekrar gönderilmeli
              </span>
            )}

            {task.requiresPhoto && (
              <span className="inline-flex items-center gap-1">
                <Camera size={12} />
                Fotoğraf
              </span>
            )}

            {task.requiresLocation && (
              <span className="inline-flex items-center gap-1">
                <MapPin size={12} />
                Konum
              </span>
            )}

            {task.requiresManagerApproval && (
              <span className="inline-flex items-center gap-1">
                <FileCheck2 size={12} />
                Onay
              </span>
            )}
          </div>
        </div>

        <ChevronRight className="shrink-0 text-[var(--missio-text-muted)]" size={20} />
      </div>
    </button>
  )
}
