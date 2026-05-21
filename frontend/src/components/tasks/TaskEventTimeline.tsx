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

function formatEventDateTime(value: string) {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return "Tarih bilinmiyor"
  }

  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date)
}

function getStatusLabel(status: string | null) {
  if (!status) {
    return null
  }

  const labels: Record<string, string> = {
    assigned: "Bekliyor",
    in_progress: "Devam ediyor",
    completed: "Tamamlandı",
    approved: "Onaylandı",
    rejected: "Reddedildi",
    cancelled: "İptal edildi",
  }

  return labels[status] ?? status
}

function humanizeEventType(eventType: string) {
  return eventType
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toLocaleUpperCase("tr-TR") + part.slice(1))
    .join(" ")
}

function getEventPresentation(event: TaskEvent): EventPresentation {
  if (
    event.event_type === "routine_task_generated" ||
    event.event_type === "routine_task_auto_generated"
  ) {
    return {
      title: "Rutin görev oluşturuldu",
      description: event.note ?? "Günlük rutin görev sisteme eklendi.",
      icon: <PlusCircle size={16} />,
      tone: "cyan",
    }
  }

  if (event.event_type === "extra_task_created") {
    return {
      title: "Ekstra görev oluşturuldu",
      description: event.note ?? "Ekstra görev sisteme eklendi.",
      icon: <PlusCircle size={16} />,
      tone: "cyan",
    }
  }

  if (event.event_type === "task_started") {
    return {
      title: "Görev başlatıldı",
      description: event.note ?? "Personel görevi işleme aldı.",
      icon: <PlayCircle size={16} />,
      tone: "amber",
    }
  }

  if (event.event_type === "task_completed") {
    return {
      title: "Görev tamamlandı",
      description: event.note ?? "Personel görevi tamamladı.",
      icon: <CheckCircle2 size={16} />,
      tone: "green",
    }
  }

  if (event.event_type === "task_attachment_uploaded") {
    return {
      title: "Fotoğraf kanıtı eklendi",
      description: event.note ?? "Göreve fotoğraf kanıtı yüklendi.",
      icon: <Camera size={16} />,
      tone: "cyan",
    }
  }

  if (event.event_type === "task_attachment_deleted") {
    return {
      title: "Fotoğraf kanıtı silindi",
      description: event.note ?? "Görevden fotoğraf kanıtı silindi.",
      icon: <Trash2 size={16} />,
      tone: "red",
    }
  }

  if (event.event_type === "task_approved") {
    return {
      title: "Görev onaylandı",
      description: event.note ?? "Görev yönetici tarafından onaylandı.",
      icon: <FileCheck2 size={16} />,
      tone: "green",
    }
  }

  if (event.event_type === "task_rejected") {
    return {
      title: "Görev reddedildi",
      description: event.note ?? "Görev yönetici tarafından reddedildi.",
      icon: <XCircle size={16} />,
      tone: "red",
    }
  }

  if (event.event_type === "task_cancelled") {
    return {
      title: "Görev iptal edildi",
      description: event.note ?? "Görev iptal edildi.",
      icon: <XCircle size={16} />,
      tone: "red",
    }
  }

  if (event.event_type === "task_updated") {
    return {
      title: "Görev güncellendi",
      description: event.note ?? "Görev bilgileri güncellendi.",
      icon: <Edit3 size={16} />,
      tone: "slate",
    }
  }

  return {
    title: humanizeEventType(event.event_type),
    description: event.note ?? "Görev üzerinde işlem yapıldı.",
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

export function TaskEventTimeline({ taskId, refreshVersion = 0 }: TaskEventTimelineProps) {
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
          setErrorMessage("İşlem geçmişi alınamadı.")
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
  }, [taskId, refreshVersion])

  return (
    <div className="mb-4 rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
            <History size={21} />
          </div>

          <div>
            <h3 className="text-sm font-black">İşlem geçmişi</h3>
            <p className="mt-1 text-xs font-semibold leading-5 text-[var(--missio-text-muted)]">
              {events.length > 0
                ? `${events.length} işlem kaydı bulundu.`
                : "Görev hareketleri burada görünecek."}
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
          Henüz işlem geçmişi yok.
        </div>
      )}

      {events.length > 0 && (
        <div className="space-y-3">
          {events.map((event, index) => {
            const presentation = getEventPresentation(event)
            const oldStatusLabel = getStatusLabel(event.old_status)
            const newStatusLabel = getStatusLabel(event.new_status)
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
                      {formatEventDateTime(event.created_at_utc)}
                    </p>
                  </div>

                  {(oldStatusLabel || newStatusLabel || hasLocation) && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {oldStatusLabel && newStatusLabel && oldStatusLabel !== newStatusLabel && (
                        <span className="rounded-full bg-white px-2.5 py-1 text-[0.62rem] font-black text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                          {oldStatusLabel} → {newStatusLabel}
                        </span>
                      )}

                      {event.user_id !== null && (
                        <span className="rounded-full bg-white px-2.5 py-1 text-[0.62rem] font-black text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                          Kullanıcı #{event.user_id}
                        </span>
                      )}

                      {hasLocation && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-1 text-[0.62rem] font-black text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                          <MapPin size={11} />
                          Konum alındı
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


