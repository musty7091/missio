import { Camera, CheckCircle2, Clock3, MapPin, PlayCircle } from "lucide-react"
import { useRef } from "react"
import type { TodayTask } from "../../types/task"
import { getActionLabel, getPriorityLabel, getStatusLabel } from "../../utils/taskLabels"

type TaskCardProps = {
  task: TodayTask
  isBusy: boolean
  onStartTask: (task: TodayTask) => void
  onCompleteTask: (task: TodayTask) => void
  onUploadPhoto: (task: TodayTask, file: File) => void
}

export function TaskCard({
  task,
  isBusy,
  onStartTask,
  onCompleteTask,
  onUploadPhoto,
}: TaskCardProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  function handleMainAction() {
    if (task.status === "assigned") {
      onStartTask(task)
      return
    }

    if (task.status === "in_progress" || task.status === "rejected") {
      onCompleteTask(task)
    }
  }

  function handlePhotoButtonClick() {
    fileInputRef.current?.click()
  }

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]

    if (!file) {
      return
    }

    onUploadPhoto(task, file)
    event.target.value = ""
  }

  const canUseMainAction =
    task.status === "assigned" || task.status === "in_progress" || task.status === "rejected"

  return (
    <article className="rounded-[1.75rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-sm transition-colors duration-300">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-[var(--missio-primary-soft)] px-3 py-1 text-xs font-bold text-teal-700 dark:text-teal-200">
              {getStatusLabel(task.status)}
            </span>
            <span className="rounded-full bg-indigo-100 px-3 py-1 text-xs font-bold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-200">
              {getPriorityLabel(task.priority)}
            </span>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
              {task.taskType === "routine" ? "Rutin" : "Ekstra"}
            </span>
          </div>

          <h3 className="text-base font-bold leading-6">{task.title}</h3>
          <p className="mt-1 text-sm leading-6 text-[var(--missio-text-muted)]">
            {task.description}
          </p>
        </div>

        <div className="rounded-2xl bg-slate-100 p-3 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
          {task.status === "completed" || task.status === "approved" ? (
            <CheckCircle2 size={22} />
          ) : (
            <Clock3 size={22} />
          )}
        </div>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--missio-border)] px-3 py-1.5 text-xs font-semibold text-[var(--missio-text-muted)]">
          <Clock3 size={14} />
          {task.time}
        </span>

        {task.requiresPhoto && (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--missio-border)] px-3 py-1.5 text-xs font-semibold text-[var(--missio-text-muted)]">
            <Camera size={14} />
            Fotoğraf
          </span>
        )}

        {task.requiresLocation && (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--missio-border)] px-3 py-1.5 text-xs font-semibold text-[var(--missio-text-muted)]">
            <MapPin size={14} />
            Konum
          </span>
        )}
      </div>

      <div className="flex gap-3">
        {task.requiresPhoto && (
          <>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleFileChange}
            />

            <button
              type="button"
              onClick={handlePhotoButtonClick}
              disabled={isBusy}
              className="flex flex-1 items-center justify-center gap-2 rounded-2xl border border-[var(--missio-border)] px-4 py-3 text-sm font-bold disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Camera size={18} />
              Fotoğraf
            </button>
          </>
        )}

        <button
          type="button"
          onClick={handleMainAction}
          disabled={!canUseMainAction || isBusy}
          className="flex flex-1 items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 py-3 text-sm font-bold text-white shadow-lg shadow-teal-500/20 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <PlayCircle size={18} />
          {isBusy ? "İşleniyor..." : getActionLabel(task.status)}
        </button>
      </div>
    </article>
  )
}
