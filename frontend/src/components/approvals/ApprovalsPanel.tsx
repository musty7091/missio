import {
  AlertCircle,
  Camera,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock3,
  FileCheck2,
  ImageIcon,
  Loader2,
  MapPin,
  MessageSquareText,
  RefreshCw,
  UserRound,
  UsersRound,
  XCircle,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import {
  approveTask,
  getTaskAttachmentFileBlob,
  listBusinessTasks,
  listTaskAttachments,
  listTaskEvents,
  rejectTask,
  type TaskAttachment,
  type TaskEvent,
} from "../../services/taskService"
import type { TodayTask } from "../../types/task"
import { mapApiTaskToTodayTask } from "../../utils/apiTaskMapper"
import { getPriorityLabel, getStatusLabel } from "../../utils/taskLabels"

type ApprovalsPanelProps = {
  businessId: number | null
  onChanged: () => void
}

type StaffApprovalGroup = {
  key: string
  assigneeId: number | null
  assigneeName: string
  assigneeUsername: string | null
  initials: string
  tasks: TodayTask[]
}

type AttachmentPreview = {
  attachment: TaskAttachment
  url: string
}

function formatTime(value: string | null) {
  if (!value) {
    return "Saat yok"
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return "Saat yok"
  }

  return date.toLocaleTimeString("tr-TR", {
    hour: "2-digit",
    minute: "2-digit",
  })
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

function groupTasksByStaff(tasks: TodayTask[]): StaffApprovalGroup[] {
  const groups = new Map<string, StaffApprovalGroup>()

  for (const task of tasks) {
    const assigneeName = getAssigneeName(task)
    const key = task.assignedToUserId
      ? `user-${task.assignedToUserId}`
      : `name-${assigneeName}`

    const existingGroup = groups.get(key)

    if (existingGroup) {
      existingGroup.tasks.push(task)
      continue
    }

    groups.set(key, {
      key,
      assigneeId: task.assignedToUserId,
      assigneeName,
      assigneeUsername: task.assignedToUsername,
      initials: getInitials(assigneeName),
      tasks: [task],
    })
  }

  return Array.from(groups.values()).sort((firstGroup, secondGroup) =>
    firstGroup.assigneeName.localeCompare(secondGroup.assigneeName, "tr-TR"),
  )
}

function getCompletedEvent(events: TaskEvent[]) {
  return [...events]
    .reverse()
    .find((event) => event.event_type === "task_completed")
}

function TaskEvidencePanel({ task }: { task: TodayTask }) {
  const [events, setEvents] = useState<TaskEvent[]>([])
  const [attachments, setAttachments] = useState<TaskAttachment[]>([])
  const [previews, setPreviews] = useState<AttachmentPreview[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const completedEvent = useMemo(() => getCompletedEvent(events), [events])
  const completionNote = completedEvent?.note?.trim()
  const hasLocation =
    completedEvent?.latitude !== null &&
    completedEvent?.latitude !== undefined &&
    completedEvent?.longitude !== null &&
    completedEvent?.longitude !== undefined

  useEffect(() => {
    let isMounted = true
    let objectUrls: string[] = []

    async function loadEvidence() {
      setIsLoading(true)
      setErrorMessage(null)

      try {
        const [attachmentResponse, eventResponse] = await Promise.all([
          listTaskAttachments(task.id),
          listTaskEvents(task.id),
        ])

        if (!isMounted) {
          return
        }

        setAttachments(attachmentResponse.attachments)
        setEvents(eventResponse.events)

        const loadedPreviews: AttachmentPreview[] = []

        for (const attachment of attachmentResponse.attachments) {
          const blob = await getTaskAttachmentFileBlob(task.id, attachment.id)
          const url = URL.createObjectURL(blob)
          objectUrls.push(url)

          loadedPreviews.push({
            attachment,
            url,
          })
        }

        if (isMounted) {
          setPreviews(loadedPreviews)
        }
      } catch (error) {
        if (isMounted) {
          if (error instanceof Error) {
            setErrorMessage(error.message)
          } else {
            setErrorMessage("Kanıt bilgileri alınamadı.")
          }

          setAttachments([])
          setEvents([])
          setPreviews([])
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    void loadEvidence()

    return () => {
      isMounted = false

      for (const url of objectUrls) {
        URL.revokeObjectURL(url)
      }
    }
  }, [task.id])

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 rounded-2xl bg-[var(--missio-page-bg)] p-3 text-xs font-black text-[var(--missio-text-muted)]">
        <Loader2 className="animate-spin" size={16} />
        Kanıt bilgileri yükleniyor...
      </div>
    )
  }

  if (errorMessage) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-3 text-xs font-black leading-5 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
        {errorMessage}
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="rounded-2xl bg-[var(--missio-page-bg)] p-3">
        <div className="mb-2 flex items-center gap-2 text-xs font-black uppercase tracking-[0.12em] text-[var(--missio-text-muted)]">
          <MessageSquareText size={14} />
          Tamamlama notu
        </div>

        <p className="text-sm font-bold leading-6 text-[var(--missio-text-main)]">
          {completionNote || "Personel tamamlama notu yazmamış."}
        </p>

        <div className="mt-3 grid grid-cols-2 gap-2 text-[0.7rem] font-bold text-[var(--missio-text-muted)]">
          <div className="rounded-2xl bg-[var(--missio-card-bg)] px-3 py-2">
            <div className="mb-1 flex items-center gap-1">
              <Clock3 size={12} />
              Tamamlanma
            </div>
            <p className="text-[var(--missio-text-main)]">
              {formatDateTime(task.completedAtUtc)}
            </p>
          </div>

          <div className="rounded-2xl bg-[var(--missio-card-bg)] px-3 py-2">
            <div className="mb-1 flex items-center gap-1">
              <MapPin size={12} />
              Konum
            </div>
            <p className="text-[var(--missio-text-main)]">
              {hasLocation ? "Alındı" : "Yok"}
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-2xl bg-[var(--missio-page-bg)] p-3">
        <div className="mb-2 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs font-black uppercase tracking-[0.12em] text-[var(--missio-text-muted)]">
            <Camera size={14} />
            Fotoğraf kanıtı
          </div>

          <span className="rounded-full bg-[var(--missio-card-bg)] px-2.5 py-1 text-[0.65rem] font-black text-[var(--missio-text-muted)]">
            {attachments.length}
          </span>
        </div>

        {attachments.length === 0 ? (
          task.requiresPhoto ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 p-3 text-xs font-black leading-5 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
              Bu görev fotoğraf kanıtı gerektiriyor; ancak fotoğraf bulunamadı.
            </div>
          ) : (
            <div className="rounded-2xl bg-[var(--missio-card-bg)] p-3 text-xs font-bold text-[var(--missio-text-muted)]">
              Bu görev için fotoğraf şartı yok.
            </div>
          )
        ) : (
          <div className="grid grid-cols-2 gap-2">
            {previews.map((preview) => (
              <div
                key={preview.attachment.id}
                className="overflow-hidden rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)]"
              >
                <img
                  src={preview.url}
                  alt={`Görev kanıtı ${preview.attachment.id}`}
                  className="h-36 w-full object-cover"
                />

                <div className="px-3 py-2 text-[0.65rem] font-bold text-[var(--missio-text-muted)]">
                  {formatDateTime(preview.attachment.created_at_utc)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function ApprovalTaskCard({
  task,
  isExpanded,
  isBusy,
  rejectNote,
  onToggle,
  onRejectNoteChange,
  onApprove,
  onReject,
}: {
  task: TodayTask
  isExpanded: boolean
  isBusy: boolean
  rejectNote: string
  onToggle: () => void
  onRejectNoteChange: (value: string) => void
  onApprove: () => void
  onReject: () => void
}) {
  return (
    <article className="overflow-hidden rounded-[1.35rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] shadow-sm">
      <button
        type="button"
        onClick={onToggle}
        className="w-full p-3 text-left active:scale-[0.995]"
      >
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200">
            <FileCheck2 size={22} />
          </div>

          <div className="min-w-0 flex-1">
            <div className="mb-2 flex flex-wrap gap-1.5">
              <span className="rounded-full bg-cyan-50 px-2 py-0.5 text-[0.6rem] font-black text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200">
                {task.taskType === "routine" ? "Rutin" : "Ekstra"}
              </span>

              <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[0.6rem] font-black text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200">
                {getStatusLabel(task.status)}
              </span>

              <span className="rounded-full bg-[var(--missio-page-bg)] px-2 py-0.5 text-[0.6rem] font-black text-[var(--missio-text-muted)]">
                {getPriorityLabel(task.priority)}
              </span>

              {task.requiresPhoto && (
                <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[0.6rem] font-black text-amber-700 dark:bg-amber-950 dark:text-amber-200">
                  <ImageIcon size={11} />
                  Foto
                </span>
              )}
            </div>

            <h3 className="truncate text-base font-black text-[var(--missio-text-main)]">
              {task.title}
            </h3>

            <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
              Tamamlanma: {formatTime(task.completedAtUtc)}
            </p>
          </div>

          {isExpanded ? (
            <ChevronDown className="mt-1 shrink-0 text-[var(--missio-text-muted)]" size={20} />
          ) : (
            <ChevronRight className="mt-1 shrink-0 text-[var(--missio-text-muted)]" size={20} />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="space-y-3 border-t border-[var(--missio-border)] px-3 pb-3 pt-3">
          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-2xl bg-[var(--missio-page-bg)] p-3">
              <p className="text-[0.62rem] font-black uppercase tracking-[0.12em] text-[var(--missio-text-muted)]">
                Durum
              </p>
              <p className="mt-1 text-sm font-black text-[var(--missio-text-main)]">
                {getStatusLabel(task.status)}
              </p>
            </div>

            <div className="rounded-2xl bg-[var(--missio-page-bg)] p-3">
              <p className="text-[0.62rem] font-black uppercase tracking-[0.12em] text-[var(--missio-text-muted)]">
                Tamamlanma
              </p>
              <p className="mt-1 text-sm font-black text-[var(--missio-text-main)]">
                {formatTime(task.completedAtUtc)}
              </p>
            </div>
          </div>

          <div className="rounded-2xl bg-[var(--missio-page-bg)] p-3">
            <p className="text-xs font-black uppercase tracking-[0.12em] text-[var(--missio-text-muted)]">
              Görev açıklaması
            </p>

            <p className="mt-2 text-sm font-bold leading-6 text-[var(--missio-text-main)]">
              {task.description || "Açıklama yok."}
            </p>
          </div>

          <TaskEvidencePanel task={task} />

          <textarea
            value={rejectNote}
            onChange={(event) => onRejectNoteChange(event.target.value)}
            placeholder="Reddetmek gerekiyorsa red nedenini yaz..."
            className="min-h-24 w-full resize-none rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-3 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
          />

          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={onReject}
              disabled={isBusy}
              className="flex min-h-12 items-center justify-center gap-2 rounded-2xl border border-red-200 bg-red-50 px-3 py-2 text-sm font-black text-red-700 transition active:scale-95 disabled:opacity-60 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
            >
              {isBusy ? <Loader2 className="animate-spin" size={18} /> : <XCircle size={18} />}
              Reddet
            </button>

            <button
              type="button"
              onClick={onApprove}
              disabled={isBusy}
              className="flex min-h-12 items-center justify-center gap-2 rounded-2xl bg-emerald-600 px-3 py-2 text-sm font-black text-white shadow-lg shadow-emerald-600/20 transition active:scale-95 disabled:opacity-60"
            >
              {isBusy ? <Loader2 className="animate-spin" size={18} /> : <CheckCircle2 size={18} />}
              Onayla
            </button>
          </div>
        </div>
      )}
    </article>
  )
}

function StaffApprovalGroupCard({
  group,
  expandedTaskId,
  busyTaskId,
  rejectNotes,
  onToggleTask,
  onRejectNoteChange,
  onApprove,
  onReject,
}: {
  group: StaffApprovalGroup
  expandedTaskId: number | null
  busyTaskId: number | null
  rejectNotes: Record<number, string>
  onToggleTask: (taskId: number) => void
  onRejectNoteChange: (taskId: number, value: string) => void
  onApprove: (task: TodayTask) => void
  onReject: (task: TodayTask) => void
}) {
  return (
    <section className="overflow-hidden rounded-[1.8rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] shadow-md shadow-slate-950/5">
      <div className="flex items-center gap-3 border-b border-[var(--missio-border)] bg-[var(--missio-page-bg)]/70 px-4 py-3">
        <div className="relative flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-3xl bg-cyan-100 text-base font-black text-cyan-800 ring-4 ring-white dark:bg-cyan-950 dark:text-cyan-200 dark:ring-slate-900">
          <span>{group.initials}</span>
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 text-xs font-black text-[var(--missio-text-muted)]">
            <UserRound size={14} />
            <span>Personel</span>
          </div>

          <h3 className="mt-0.5 truncate text-base font-black text-[var(--missio-text-main)]">
            {group.assigneeName}
          </h3>

          {group.assigneeUsername && (
            <p className="mt-0.5 truncate text-xs font-bold text-[var(--missio-text-muted)]">
              @{group.assigneeUsername}
            </p>
          )}
        </div>

        <div className="rounded-2xl bg-white px-3 py-2 text-center shadow-sm dark:bg-slate-900">
          <p className="text-lg font-black leading-none text-[var(--missio-text-main)]">
            {group.tasks.length}
          </p>
          <p className="mt-1 text-[0.6rem] font-black uppercase tracking-wide text-[var(--missio-text-muted)]">
            Onay
          </p>
        </div>
      </div>

      <div className="space-y-2.5 p-3">
        {group.tasks.map((task) => (
          <ApprovalTaskCard
            key={task.id}
            task={task}
            isExpanded={expandedTaskId === task.id}
            isBusy={busyTaskId === task.id}
            rejectNote={rejectNotes[task.id] ?? ""}
            onToggle={() => onToggleTask(task.id)}
            onRejectNoteChange={(value) => onRejectNoteChange(task.id, value)}
            onApprove={() => onApprove(task)}
            onReject={() => onReject(task)}
          />
        ))}
      </div>
    </section>
  )
}

export function ApprovalsPanel({ businessId, onChanged }: ApprovalsPanelProps) {
  const [approvalTasks, setApprovalTasks] = useState<TodayTask[]>([])
  const [expandedTaskId, setExpandedTaskId] = useState<number | null>(null)
  const [rejectNotes, setRejectNotes] = useState<Record<number, string>>({})
  const [busyTaskId, setBusyTaskId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const groupedApprovalTasks = useMemo(
    () => groupTasksByStaff(approvalTasks),
    [approvalTasks],
  )

  async function loadApprovals() {
    if (!businessId) {
      setApprovalTasks([])
      setErrorMessage("Bu kullanıcı için işletme bilgisi bulunamadı.")
      return
    }

    setIsLoading(true)
    setErrorMessage(null)

    try {
      const response = await listBusinessTasks({
        businessId,
        limit: 500,
        offset: 0,
      })

      const tasks = response.tasks
        .map(mapApiTaskToTodayTask)
        .filter((task) => task.requiresManagerApproval && task.status === "completed")

      setApprovalTasks(tasks)
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Onay bekleyen görevler alınamadı.")
      }

      setApprovalTasks([])
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadApprovals()
  }, [businessId])

  async function handleApprove(task: TodayTask) {
    setBusyTaskId(task.id)
    setErrorMessage(null)

    try {
      await approveTask(task.id, {
        note: "Yönetici tarafından onaylandı.",
      })

      await loadApprovals()
      onChanged()
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Görev onaylanamadı.")
      }
    } finally {
      setBusyTaskId(null)
    }
  }

  async function handleReject(task: TodayTask) {
    const note = (rejectNotes[task.id] ?? "").trim()

    if (note.length < 2) {
      setErrorMessage("Reddetmek için en az 2 karakterlik açıklama yazılmalıdır.")
      return
    }

    setBusyTaskId(task.id)
    setErrorMessage(null)

    try {
      await rejectTask(task.id, { note })

      await loadApprovals()
      onChanged()
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Görev reddedilemedi.")
      }
    } finally {
      setBusyTaskId(null)
    }
  }

  function handleToggleTask(taskId: number) {
    setExpandedTaskId((currentTaskId) =>
      currentTaskId === taskId ? null : taskId,
    )
  }

  function handleRejectNoteChange(taskId: number, value: string) {
    setRejectNotes((currentNotes) => ({
      ...currentNotes,
      [taskId]: value,
    }))
  }

  return (
    <section className="flex flex-1 flex-col pb-24">
      <div className="mb-4 rounded-[1.7rem] bg-slate-950 p-4 text-white shadow-xl shadow-slate-950/15">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-black text-cyan-200">
              <FileCheck2 size={14} />
              Yönetici onayı
            </div>

            <h2 className="mt-3 text-2xl font-black leading-tight">
              Kanıtlı onay ekranı
            </h2>

            <p className="mt-2 text-sm font-semibold leading-5 text-slate-300">
              Personelin tamamladığı işleri not, fotoğraf ve durum bilgisiyle kontrol et.
            </p>
          </div>

          <button
            type="button"
            onClick={() => void loadApprovals()}
            disabled={isLoading}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/10 text-cyan-200 transition active:scale-95 disabled:opacity-60"
            aria-label="Yenile"
            title="Yenile"
          >
            <RefreshCw size={19} />
          </button>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-2">
          <div className="rounded-2xl bg-white/10 px-3 py-2">
            <p className="text-xl font-black leading-none">{approvalTasks.length}</p>
            <p className="mt-1 text-[0.64rem] font-bold text-slate-300">
              Onay bekleyen
            </p>
          </div>

          <div className="rounded-2xl bg-white/10 px-3 py-2">
            <div className="flex items-center gap-1.5">
              <UsersRound size={17} className="text-cyan-200" />
              <p className="text-xl font-black leading-none">
                {groupedApprovalTasks.length}
              </p>
            </div>
            <p className="mt-1 text-[0.64rem] font-bold text-slate-300">
              İlgili personel
            </p>
          </div>
        </div>
      </div>

      {errorMessage && (
        <div className="mb-3 flex gap-2 rounded-[1.4rem] border border-red-200 bg-red-50 p-3 text-sm font-black text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
          <AlertCircle size={18} />
          <span>{errorMessage}</span>
        </div>
      )}

      {isLoading ? (
        <div className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 text-sm font-black text-[var(--missio-text-muted)]">
          Onay bekleyen görevler yükleniyor...
        </div>
      ) : approvalTasks.length === 0 ? (
        <div className="flex flex-1 items-center justify-center rounded-[1.7rem] border border-dashed border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-6 text-center">
          <div>
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-3xl bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200">
              <CheckCircle2 size={28} />
            </div>

            <h3 className="mt-4 text-lg font-black">Onay bekleyen görev yok</h3>

            <p className="mt-2 text-sm font-semibold leading-6 text-[var(--missio-text-muted)]">
              Personel onay gerektiren bir görevi tamamladığında burada görünecek.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {groupedApprovalTasks.map((group) => (
            <StaffApprovalGroupCard
              key={group.key}
              group={group}
              expandedTaskId={expandedTaskId}
              busyTaskId={busyTaskId}
              rejectNotes={rejectNotes}
              onToggleTask={handleToggleTask}
              onRejectNoteChange={handleRejectNoteChange}
              onApprove={(task) => void handleApprove(task)}
              onReject={(task) => void handleReject(task)}
            />
          ))}
        </div>
      )}
    </section>
  )
}
