import {
  Camera,
  CheckCircle2,
  CircleDot,
  Clock3,
  Edit3,
  FileCheck2,
  History,
  Loader2,
  MapPin,
  PlayCircle,
  PlusCircle,
  Trash2,
  XCircle,
} from "lucide-react"
import type { ReactNode } from "react"
import { useEffect, useState } from "react"
import { useTranslation, type TranslationKey } from "../../i18n/language"
import { listTaskEvents, type TaskEvent } from "../../services/taskService"

type TaskEventTimelineProps = {
  taskId: number
  refreshVersion?: number
}

type EventPresentation = {
  title: string
  description: string
  icon: ReactNode
  tone: "cyan" | "green" | "amber" | "red" | "slate"
}

function formatEventDateTime(
  value: string,
  language: "tr" | "en",
  t: (key: TranslationKey) => string,
) {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return t("task.timeline.unknownDate")
  }

  return new Intl.DateTimeFormat(language === "tr" ? "tr-TR" : "en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date)
}

function getStatusLabel(
  status: string | null,
  t: (key: TranslationKey) => string,
) {
  if (!status) {
    return null
  }

  if (status === "assigned") return t("task.status.assigned")
  if (status === "in_progress") return t("task.status.inProgress")
  if (status === "completed") return t("task.status.completedNoApproval")
  if (status === "approved") return t("task.status.approved")
  if (status === "rejected") return t("task.status.rejected")
  if (status === "cancelled") return t("task.status.cancelled")

  return status
}

function humanizeEventType(eventType: string) {
  return eventType
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ")
}

function getSystemEventNote(
  event: TaskEvent,
  fallbackKey: TranslationKey,
  t: (key: TranslationKey) => string,
) {
  const note = event.note?.trim()

  if (!note) {
    return t(fallbackKey)
  }

  if (
    note === "Günlük rutin görev otomatik oluşturuldu." ||
    note === "Daily routine task was created automatically."
  ) {
    return t("task.timeline.note.dailyRoutineAutoCreated")
  }

  return note
}

function getEventPresentation(
  event: TaskEvent,
  t: (key: TranslationKey) => string,
): EventPresentation {
  if (
    event.event_type === "routine_task_generated" ||
    event.event_type === "routine_task_auto_generated"
  ) {
    return {
      title: t("task.timeline.event.routineGeneratedTitle"),
      description: getSystemEventNote(
        event,
        "task.timeline.event.routineGeneratedDescription",
        t,
      ),
      icon: <PlusCircle size={16} />,
      tone: "cyan",
    }
  }

  if (event.event_type === "extra_task_created") {
    return {
      title: t("task.timeline.event.extraCreatedTitle"),
      description: getSystemEventNote(
        event,
        "task.timeline.event.extraCreatedDescription",
        t,
      ),
      icon: <PlusCircle size={16} />,
      tone: "cyan",
    }
  }

  if (event.event_type === "task_started") {
    return {
      title: t("task.timeline.event.startedTitle"),
      description: getSystemEventNote(
        event,
        "task.timeline.event.startedDescription",
        t,
      ),
      icon: <PlayCircle size={16} />,
      tone: "amber",
    }
  }

  if (event.event_type === "task_completed") {
    return {
      title: t("task.timeline.event.completedTitle"),
      description: getSystemEventNote(
        event,
        "task.timeline.event.completedDescription",
        t,
      ),
      icon: <CheckCircle2 size={16} />,
      tone: "green",
    }
  }

  if (event.event_type === "task_attachment_uploaded") {
    return {
      title: t("task.timeline.event.attachmentUploadedTitle"),
      description: getSystemEventNote(
        event,
        "task.timeline.event.attachmentUploadedDescription",
        t,
      ),
      icon: <Camera size={16} />,
      tone: "cyan",
    }
  }

  if (event.event_type === "task_attachment_deleted") {
    return {
      title: t("task.timeline.event.attachmentDeletedTitle"),
      description: getSystemEventNote(
        event,
        "task.timeline.event.attachmentDeletedDescription",
        t,
      ),
      icon: <Trash2 size={16} />,
      tone: "red",
    }
  }

  if (event.event_type === "task_approved") {
    return {
      title: t("task.timeline.event.approvedTitle"),
      description: getSystemEventNote(
        event,
        "task.timeline.event.approvedDescription",
        t,
      ),
      icon: <FileCheck2 size={16} />,
      tone: "green",
    }
  }

  if (event.event_type === "task_rejected") {
    return {
      title: t("task.timeline.event.rejectedTitle"),
      description: getSystemEventNote(
        event,
        "task.timeline.event.rejectedDescription",
        t,
      ),
      icon: <XCircle size={16} />,
      tone: "red",
    }
  }

  if (event.event_type === "task_cancelled") {
    return {
      title: t("task.timeline.event.cancelledTitle"),
      description: getSystemEventNote(
        event,
        "task.timeline.event.cancelledDescription",
        t,
      ),
      icon: <XCircle size={16} />,
      tone: "red",
    }
  }

  if (event.event_type === "task_updated") {
    return {
      title: t("task.timeline.event.updatedTitle"),
      description: getSystemEventNote(
        event,
        "task.timeline.event.updatedDescription",
        t,
      ),
      icon: <Edit3 size={16} />,
      tone: "slate",
    }
  }

  return {
    title: humanizeEventType(event.event_type),
    description: event.note ?? t("task.timeline.event.defaultDescription"),
    icon: <CircleDot size={16} />,
    tone: "slate",
  }
}

function getToneClasses(tone: EventPresentation["tone"]) {
  const classes = {
    cyan: "bg-cyan-500 text-white shadow-cyan-500/20",
    green: "bg-emerald-500 text-white shadow-emerald-500/20",
    amber: "bg-amber-400 text-slate-950 shadow-amber-500/20",
    red: "bg-red-500 text-white shadow-red-500/20",
    slate: "bg-slate-700 text-white shadow-slate-500/20",
  }

  return classes[tone]
}

function getRecordCountText(
  count: number,
  t: (key: TranslationKey) => string,
) {
  const key =
    count === 1 ? "task.timeline.recordFound" : "task.timeline.recordsFound"

  return `${count} ${t(key)}`
}

export function TaskEventTimeline({ taskId, refreshVersion = 0 }: TaskEventTimelineProps) {
  const { language, t } = useTranslation()
  const [events, setEvents] = useState<TaskEvent[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true

    async function loadEvents() {
      setIsLoading(true)
      setErrorMessage(null)

      try {
        const response = await listTaskEvents(taskId)

        if (isMounted) {
          setEvents(response.events)
        }
      } catch (error) {
        if (!isMounted) {
          return
        }

        setEvents([])

        if (error instanceof Error) {
          setErrorMessage(error.message)
        } else {
          setErrorMessage(t("task.timeline.loadError"))
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    void loadEvents()

    return () => {
      isMounted = false
    }
  }, [taskId, refreshVersion, t])

  return (
    <div className="mb-4 rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
            <History size={21} />
          </div>

          <div>
            <h3 className="text-sm font-black">{t("task.timeline.title")}</h3>
            <p className="mt-1 text-xs font-semibold leading-5 text-[var(--missio-text-muted)]">
              {events.length > 0
                ? getRecordCountText(events.length, t)
                : t("task.timeline.emptyPreview")}
            </p>
          </div>
        </div>

        {isLoading && <Loader2 className="mt-2 animate-spin text-cyan-600" size={18} />}
      </div>

      {errorMessage && (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-bold text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
          {errorMessage}
        </div>
      )}

      {!isLoading && !errorMessage && events.length === 0 && (
        <div className="flex items-center gap-3 rounded-2xl border border-dashed border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3 text-sm font-bold text-[var(--missio-text-muted)]">
          <Clock3 size={19} />
          {t("task.timeline.empty")}
        </div>
      )}

      {events.length > 0 && (
        <div className="space-y-3">
          {events.map((event, index) => {
            const presentation = getEventPresentation(event, t)
            const oldStatusLabel = getStatusLabel(event.old_status, t)
            const newStatusLabel = getStatusLabel(event.new_status, t)
            const hasLocation = event.latitude !== null && event.longitude !== null

            return (
              <div key={event.id} className="relative flex gap-3">
                <div className="flex flex-col items-center">
                  <div
                    className={`flex h-9 w-9 items-center justify-center rounded-2xl shadow-lg ${getToneClasses(
                      presentation.tone,
                    )}`}
                  >
                    {presentation.icon}
                  </div>

                  {index < events.length - 1 && (
                    <div className="mt-2 h-full min-h-[2rem] w-px bg-[var(--missio-border)]" />
                  )}
                </div>

                <div className="min-w-0 flex-1 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-3 py-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-sm font-black text-[var(--missio-text-main)]">
                        {presentation.title}
                      </p>
                      <p className="mt-1 text-xs font-bold leading-5 text-[var(--missio-text-muted)]">
                        {presentation.description}
                      </p>
                    </div>

                    <p className="shrink-0 text-right text-[0.65rem] font-black text-[var(--missio-text-muted)]">
                      {formatEventDateTime(event.created_at_utc, language, t)}
                    </p>
                  </div>

                  {(oldStatusLabel || newStatusLabel || hasLocation || event.user_id !== null) && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {oldStatusLabel && newStatusLabel && oldStatusLabel !== newStatusLabel && (
                        <span className="rounded-full bg-white px-2.5 py-1 text-[0.62rem] font-black text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                          {oldStatusLabel} → {newStatusLabel}
                        </span>
                      )}

                      {event.user_id !== null && (
                        <span className="rounded-full bg-white px-2.5 py-1 text-[0.62rem] font-black text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                          {t("task.timeline.userPrefix")} #{event.user_id}
                        </span>
                      )}

                      {hasLocation && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-1 text-[0.62rem] font-black text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                          <MapPin size={11} />
                          {t("task.timeline.locationCaptured")}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
