import {
  AlertCircle,
  ArrowLeft,
  Camera,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  FileCheck2,
  Flag,
  ImageIcon,
  Loader2,
  MapPin,
  MessageSquareText,
  PlayCircle,
  ShieldCheck,
  Trash2,
  X,
  ZoomIn,
} from "lucide-react"
import type { ChangeEvent, ReactNode } from "react"
import { useEffect, useRef, useState } from "react"
import { useTranslation, type TranslationKey } from "../../i18n/language"
import {
  deleteTaskAttachment,
  getTaskAttachmentFileBlob,
  listTaskAttachments,
  type TaskAttachment,
} from "../../services/taskService"
import type { TaskPriority, TaskStatus, TodayTask } from "../../types/task"
import { TaskEventTimeline } from "./TaskEventTimeline"

type TaskDetailPanelProps = {
  task: TodayTask
  isBusy: boolean
  onClose: () => void
  onStartTask: (task: TodayTask) => Promise<void>
  onCompleteTask: (task: TodayTask, note?: string) => Promise<void>
  onUploadPhoto: (task: TodayTask, file: File) => Promise<void>
}

type AttachmentPreview = {
  attachment: TaskAttachment
  objectUrl: string
}

function DetailChip({
  icon,
  label,
}: {
  icon: ReactNode
  label: string
}) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-3 py-1.5 text-xs font-black text-[var(--missio-text-muted)]">
      {icon}
      {label}
    </span>
  )
}

function DetailInfoRow({
  icon,
  label,
  value,
}: {
  icon: ReactNode
  label: string
  value: string
}) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
        {icon}
      </div>

      <div className="min-w-0">
        <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--missio-text-muted)]">
          {label}
        </p>
        <p className="mt-1 text-sm font-black text-[var(--missio-text-main)]">
          {value}
        </p>
      </div>
    </div>
  )
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

function getDetailGuidance(
  task: TodayTask,
  t: (key: TranslationKey) => string,
) {
  if (task.status === "assigned") {
    return t("task.detail.guidance.assigned")
  }

  if (task.status === "in_progress") {
    if (task.requiresPhoto) {
      return t("task.detail.guidance.inProgressWithPhoto")
    }

    return t("task.detail.guidance.inProgress")
  }

  if (task.status === "completed") {
    if (task.requiresManagerApproval) {
      return t("task.detail.guidance.completedWaitingApproval")
    }

    return t("task.detail.guidance.completed")
  }

  if (task.status === "approved") {
    return t("task.detail.guidance.approved")
  }

  if (task.status === "rejected") {
    return t("task.detail.guidance.rejected")
  }

  if (task.status === "cancelled") {
    return t("task.detail.guidance.cancelled")
  }

  return t("task.detail.guidance.default")
}

function getDetailStatusLabel(
  task: TodayTask,
  t: (key: TranslationKey) => string,
) {
  if (task.status === "completed" && !task.requiresManagerApproval) {
    return t("task.status.completedNoApproval")
  }

  return t(getStatusTranslationKey(task.status))
}

function getActionButtonLabel(
  task: TodayTask,
  t: (key: TranslationKey) => string,
) {
  if (task.status === "assigned") {
    return t("task.detail.action.start")
  }

  if (task.status === "in_progress") {
    return t("task.detail.action.complete")
  }

  if (task.status === "rejected") {
    return t("task.detail.action.resubmit")
  }

  if (
    task.status === "completed" ||
    task.status === "approved" ||
    task.status === "cancelled"
  ) {
    return t("task.action.detail")
  }

  return t("task.action.open")
}

function getClosedTaskLabel(
  task: TodayTask,
  t: (key: TranslationKey) => string,
) {
  if (task.status === "approved") {
    return t("task.detail.closed.approved")
  }

  if (task.status === "cancelled") {
    return t("task.detail.closed.cancelled")
  }

  if (task.status === "completed" && task.requiresManagerApproval) {
    return t("task.detail.closed.waitingApproval")
  }

  return t("task.detail.closed.completed")
}

function getTaskTypeLabel(
  task: TodayTask,
  t: (key: TranslationKey) => string,
) {
  return task.taskType === "routine"
    ? t("task.type.routine")
    : t("task.type.oneTime")
}

function getTaskTypeDetailLabel(
  task: TodayTask,
  t: (key: TranslationKey) => string,
) {
  return task.taskType === "routine"
    ? t("task.detail.routineTask")
    : t("task.detail.oneTimeTask")
}

function formatFileSize(
  fileSize: number | null,
  t: (key: TranslationKey) => string,
) {
  if (!fileSize || fileSize <= 0) {
    return t("task.detail.fileSizeUnknown")
  }

  if (fileSize < 1024 * 1024) {
    return `${Math.round(fileSize / 1024)} KB`
  }

  return `${(fileSize / 1024 / 1024).toFixed(1)} MB`
}

export function TaskDetailPanel({
  task,
  isBusy,
  onClose,
  onStartTask,
  onCompleteTask,
  onUploadPhoto,
}: TaskDetailPanelProps) {
  const { t } = useTranslation()
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const photoPreviewHistoryTokenRef = useRef<string | null>(null)

  const [attachmentPreviews, setAttachmentPreviews] = useState<AttachmentPreview[]>([])
  const [isLoadingAttachments, setIsLoadingAttachments] = useState(false)
  const [attachmentErrorMessage, setAttachmentErrorMessage] = useState<string | null>(null)
  const [actionErrorMessage, setActionErrorMessage] = useState<string | null>(null)
  const [shouldFlashPhotoButton, setShouldFlashPhotoButton] = useState(false)
  const photoButtonFlashTimeoutRef = useRef<number | null>(null)
  const [deletingAttachmentId, setDeletingAttachmentId] = useState<number | null>(null)
  const [selectedPreview, setSelectedPreview] = useState<AttachmentPreview | null>(null)
  const [timelineRefreshVersion, setTimelineRefreshVersion] = useState(0)
  const [completionNote, setCompletionNote] = useState("")

  const taskTimeLabel = task.dueAtUtc ? task.time : t("task.card.today")

  const canUseMainAction =
    task.status === "assigned" || task.status === "in_progress" || task.status === "rejected"

  const isClosedTask =
    task.status === "completed" ||
    task.status === "approved" ||
    task.status === "cancelled"

  const canDeleteAttachments = !isClosedTask

  const canWriteCompletionNote =
    task.status === "in_progress" || task.status === "rejected"

  const referenceAttachmentPreviews = attachmentPreviews.filter(
    (preview) => preview.attachment.attachment_type === "reference",
  )

  const evidenceAttachmentPreviews = attachmentPreviews.filter(
    (preview) => preview.attachment.attachment_type === "evidence",
  )

  const voiceNotePreviews = attachmentPreviews.filter(
    (preview) => preview.attachment.attachment_type === "voice_note",
  )

  function triggerPhotoButtonFlash() {
    setShouldFlashPhotoButton(true)

    if (photoButtonFlashTimeoutRef.current !== null) {
      window.clearTimeout(photoButtonFlashTimeoutRef.current)
    }

    photoButtonFlashTimeoutRef.current = window.setTimeout(() => {
      setShouldFlashPhotoButton(false)
      photoButtonFlashTimeoutRef.current = null
    }, 3000)
  }

  async function loadAttachments() {
    setIsLoadingAttachments(true)
    setAttachmentErrorMessage(null)

    try {
      const response = await listTaskAttachments(task.id)

      const previews = await Promise.all(
        response.attachments.map(async (attachment) => {
          const blob = await getTaskAttachmentFileBlob(task.id, attachment.id)

          return {
            attachment,
            objectUrl: URL.createObjectURL(blob),
          }
        }),
      )

      setAttachmentPreviews((currentPreviews) => {
        currentPreviews.forEach((preview) => URL.revokeObjectURL(preview.objectUrl))
        return previews
      })
    } catch (error) {
      setAttachmentPreviews((currentPreviews) => {
        currentPreviews.forEach((preview) => URL.revokeObjectURL(preview.objectUrl))
        return []
      })

      if (error instanceof Error) {
        setAttachmentErrorMessage(error.message)
      } else {
        setAttachmentErrorMessage(t("task.detail.attachmentsLoadError"))
      }
    } finally {
      setIsLoadingAttachments(false)
    }
  }

  useEffect(() => {
    setCompletionNote("")
    setActionErrorMessage(null)
    setShouldFlashPhotoButton(false)

    if (photoButtonFlashTimeoutRef.current !== null) {
      window.clearTimeout(photoButtonFlashTimeoutRef.current)
      photoButtonFlashTimeoutRef.current = null
    }

    void loadAttachments()

    return () => {
      setAttachmentPreviews((currentPreviews) => {
        currentPreviews.forEach((preview) => URL.revokeObjectURL(preview.objectUrl))
        return []
      })
    }
  }, [task.id])

  function openPhotoPreview(preview: AttachmentPreview) {
    const historyToken = `missio-photo-preview-${preview.attachment.id}-${Date.now()}`
    photoPreviewHistoryTokenRef.current = historyToken

    window.history.pushState(
      {
        ...(window.history.state ?? {}),
        missioPhotoPreviewToken: historyToken,
      },
      "",
      window.location.href,
    )

    setSelectedPreview(preview)
  }

  function closePhotoPreview() {
    if (
      selectedPreview !== null &&
      photoPreviewHistoryTokenRef.current !== null &&
      window.history.state?.missioPhotoPreviewToken === photoPreviewHistoryTokenRef.current
    ) {
      window.history.back()
      return
    }

    photoPreviewHistoryTokenRef.current = null
    setSelectedPreview(null)
  }

  useEffect(() => {
    function handlePhotoPreviewBack(event: PopStateEvent) {
      if (selectedPreview === null) {
        return
      }

      const stillInsidePhotoPreview =
        photoPreviewHistoryTokenRef.current !== null &&
        event.state?.missioPhotoPreviewToken === photoPreviewHistoryTokenRef.current

      if (stillInsidePhotoPreview) {
        return
      }

      photoPreviewHistoryTokenRef.current = null
      setSelectedPreview(null)
    }

    window.addEventListener("popstate", handlePhotoPreviewBack)

    return () => {
      window.removeEventListener("popstate", handlePhotoPreviewBack)
    }
  }, [selectedPreview])

  async function handleMainAction() {
    setActionErrorMessage(null)

    if (task.status === "assigned") {
      try {
        await onStartTask(task)
        setTimelineRefreshVersion((currentVersion) => currentVersion + 1)
      } catch (error) {
        if (error instanceof Error) {
          setActionErrorMessage(error.message)
        } else {
          setActionErrorMessage(t("task.detail.startError"))
        }
      }

      return
    }

    if (task.status === "in_progress" || task.status === "rejected") {
      if (task.requiresPhoto && evidenceAttachmentPreviews.length < 1) {
        triggerPhotoButtonFlash()
        return
      }

      try {
        await onCompleteTask(task, completionNote.trim() || undefined)
        setCompletionNote("")
        setTimelineRefreshVersion((currentVersion) => currentVersion + 1)
      } catch (error) {
        if (error instanceof Error) {
          setActionErrorMessage(error.message)
        } else {
          setActionErrorMessage(t("task.detail.completeError"))
        }
      }
    }
  }

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]

    if (!file) {
      return
    }

    try {
      await onUploadPhoto(task, file)
      await loadAttachments()
      setTimelineRefreshVersion((currentVersion) => currentVersion + 1)
    } finally {
      event.target.value = ""
    }
  }

  async function handleDeleteAttachment(attachmentId: number) {
    const confirmed = window.confirm(t("task.detail.confirmDeletePhoto"))

    if (!confirmed) {
      return
    }

    setDeletingAttachmentId(attachmentId)
    setAttachmentErrorMessage(null)

    try {
      await deleteTaskAttachment(task.id, attachmentId)
      await loadAttachments()
      setTimelineRefreshVersion((currentVersion) => currentVersion + 1)
    } catch (error) {
      if (error instanceof Error) {
        setAttachmentErrorMessage(error.message)
      } else {
        setAttachmentErrorMessage(t("task.detail.photoDeleteError"))
      }
    } finally {
      setDeletingAttachmentId(null)
    }
  }

  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center px-3 pb-3">
      <button
        type="button"
        className="absolute inset-0 bg-slate-950/50 backdrop-blur-sm"
        aria-label={t("task.detail.closeDetail")}
        onClick={onClose}
      />

      <section className="relative z-10 max-h-[88vh] w-full max-w-md overflow-hidden rounded-[2rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] shadow-2xl shadow-slate-950/30">
        <div className="max-h-[88vh] overflow-y-auto p-4">
          <div className="mx-auto mb-3 h-1.5 w-12 rounded-full bg-slate-300 dark:bg-slate-700" />

          <div className="mb-4 overflow-hidden rounded-[1.75rem] bg-slate-950 p-4 text-white shadow-xl shadow-slate-900/20">
            <div className="relative">
              <div className="absolute -right-12 -top-12 h-36 w-36 rounded-full border border-cyan-300/20" />
              <div className="absolute right-5 top-9 h-3 w-3 rounded-full bg-cyan-300 shadow-lg shadow-cyan-300/50" />

              <div className="relative flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan-300">
                    {t("task.detail.title")}
                  </p>

                  <h2 className="mt-2 text-3xl font-black leading-tight tracking-tight">
                    {task.title}
                  </h2>

                  <p className="mt-2 text-sm font-semibold leading-5 text-slate-300">
                    {getTaskTypeDetailLabel(task, t)} · {taskTimeLabel}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={onClose}
                  className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/10 text-white"
                  aria-label={t("task.detail.close")}
                >
                  <X size={20} />
                </button>
              </div>

              <div className="relative mt-4 flex flex-wrap gap-2">
                <span className="rounded-full bg-cyan-300 px-3 py-1.5 text-xs font-black text-slate-950">
                  {getDetailStatusLabel(task, t)}
                </span>

                <span className="rounded-full bg-white/10 px-3 py-1.5 text-xs font-black text-slate-200">
                  {t(getPriorityTranslationKey(task.priority))}
                </span>

                <span className="rounded-full bg-white/10 px-3 py-1.5 text-xs font-black text-slate-200">
                  {getTaskTypeLabel(task, t)}
                </span>
              </div>
            </div>
          </div>

          <div className="mb-4 rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
                <ShieldCheck size={21} />
              </div>

              <div>
                <h3 className="text-sm font-black">{t("task.detail.operationStatus")}</h3>
                <p className="mt-1 text-sm font-semibold leading-6 text-[var(--missio-text-muted)]">
                  {getDetailGuidance(task, t)}
                </p>
              </div>
            </div>
          </div>

          <div className="mb-4 overflow-hidden rounded-[1.6rem] border border-cyan-200 bg-cyan-50/70 shadow-sm dark:border-cyan-900 dark:bg-cyan-950/30">
            <div className="flex">
              <div className="w-1.5 shrink-0 bg-cyan-400" />

              <div className="flex flex-1 items-start gap-3 p-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-cyan-500 text-white shadow-lg shadow-cyan-500/20">
                  <ClipboardCheck size={21} />
                </div>

                <div className="min-w-0">
                  <p className="text-xs font-black uppercase tracking-[0.18em] text-cyan-700 dark:text-cyan-200">
                    {t("task.detail.workToDo")}
                  </p>

                  <h3 className="mt-1 text-base font-black text-slate-950 dark:text-white">
                    {t("task.detail.descriptionTitle")}
                  </h3>

                  <p className="mt-2 text-base font-bold leading-7 text-slate-700 dark:text-slate-200">
                    {task.description || t("task.detail.noDescription")}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {referenceAttachmentPreviews.length > 0 && (
            <div className="mb-4 rounded-[1.5rem] border border-cyan-200 bg-cyan-50/70 p-4 dark:border-cyan-900 dark:bg-cyan-950/30">
              <div className="mb-3 flex items-start gap-3">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-cyan-500 text-white shadow-lg shadow-cyan-500/20">
                  <ImageIcon size={21} />
                </div>

                <div>
                  <h3 className="text-sm font-black text-slate-950 dark:text-white">
                    {t("task.detail.referenceImage")}
                  </h3>
                  <p className="mt-1 text-xs font-semibold leading-5 text-slate-700 dark:text-slate-200">
                    {t("task.detail.referenceImageDescription")}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2">
                {referenceAttachmentPreviews.map((preview) => (
                  <button
                    key={preview.attachment.id}
                    type="button"
                    onClick={() => openPhotoPreview(preview)}
                    className="group relative overflow-hidden rounded-2xl border border-cyan-200 bg-white text-left shadow-sm active:scale-[0.98] dark:border-cyan-900 dark:bg-slate-950"
                  >
                    <img
                      src={preview.objectUrl}
                      alt={preview.attachment.file_name}
                      className="aspect-square w-full object-cover transition group-active:scale-95"
                    />

                    <span className="absolute right-1.5 top-1.5 flex h-7 w-7 items-center justify-center rounded-full bg-slate-950/70 text-white backdrop-blur-sm">
                      <ZoomIn size={14} />
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {voiceNotePreviews.length > 0 && (
            <div className="mb-4 rounded-[1.5rem] border border-violet-200 bg-violet-50/70 p-4 dark:border-violet-900 dark:bg-violet-950/30">
              <div className="mb-3 flex items-start gap-3">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-violet-500 text-white shadow-lg shadow-violet-500/20">
                  <MessageSquareText size={21} />
                </div>

                <div>
                  <h3 className="text-sm font-black text-slate-950 dark:text-white">
                    {t("task.detail.voiceTaskNote")}
                  </h3>
                  <p className="mt-1 text-xs font-semibold leading-5 text-slate-700 dark:text-slate-200">
                    {t("task.detail.voiceTaskNoteDescription")}
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                {voiceNotePreviews.map((preview) => (
                  <div
                    key={preview.attachment.id}
                    className="rounded-2xl border border-violet-200 bg-white p-3 shadow-sm dark:border-violet-900 dark:bg-slate-950"
                  >
                    <div className="mb-2 flex items-center justify-between gap-3">
                      <p className="truncate text-xs font-black text-slate-950 dark:text-white">
                        {t("task.detail.voiceNote")}
                      </p>
                      <p className="shrink-0 text-[0.65rem] font-bold text-slate-500 dark:text-slate-400">
                        {formatFileSize(preview.attachment.file_size, t)}
                      </p>
                    </div>

                    <audio
                      controls
                      src={preview.objectUrl}
                      className="w-full"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="mb-4 grid grid-cols-1 gap-3">
            <DetailInfoRow
              icon={<Clock3 size={19} />}
              label={t("task.detail.taskTime")}
              value={taskTimeLabel}
            />

            <DetailInfoRow
              icon={<Flag size={19} />}
              label={t("task.detail.priority")}
              value={t(getPriorityTranslationKey(task.priority))}
            />
          </div>

          <div className="mb-4 rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4">
            <h3 className="text-sm font-black">{t("task.detail.requirements")}</h3>

            <div className="mt-3 flex flex-wrap gap-2">
              {task.requiresPhoto ? (
                <DetailChip icon={<Camera size={14} />} label={t("task.detail.photoRequired")} />
              ) : (
                <DetailChip icon={<Camera size={14} />} label={t("task.detail.photoNotRequired")} />
              )}

              {task.requiresLocation ? (
                <DetailChip icon={<MapPin size={14} />} label={t("task.detail.locationRequired")} />
              ) : (
                <DetailChip icon={<MapPin size={14} />} label={t("task.detail.locationNotRequired")} />
              )}

              {task.requiresManagerApproval ? (
                <DetailChip icon={<FileCheck2 size={14} />} label={t("task.detail.managerApprovalRequired")} />
              ) : (
                <DetailChip icon={<FileCheck2 size={14} />} label={t("task.detail.managerApprovalNotRequired")} />
              )}
            </div>
          </div>

          {task.requiresPhoto && (
            <div className="mb-4 rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-4">
              <div className="mb-3 flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
                    <Camera size={21} />
                  </div>

                  <div>
                    <h3 className="text-sm font-black">{t("task.detail.evidencePhoto")}</h3>
                    <p className="mt-1 text-xs font-semibold leading-5 text-[var(--missio-text-muted)]">
                      {evidenceAttachmentPreviews.length > 0
                        ? `${evidenceAttachmentPreviews.length} ${t("task.detail.evidencePhotoAdded")}`
                        : t("task.detail.evidencePhotoNotAdded")}
                    </p>
                  </div>
                </div>

                {isLoadingAttachments && (
                  <Loader2 className="mt-2 animate-spin text-cyan-600" size={18} />
                )}
              </div>

              {attachmentErrorMessage && (
                <div className="rounded-2xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-bold text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
                  {attachmentErrorMessage}
                </div>
              )}

              {!isLoadingAttachments && !attachmentErrorMessage && evidenceAttachmentPreviews.length === 0 && (
                <div className="flex items-center gap-3 rounded-2xl border border-dashed border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-3 text-sm font-bold text-[var(--missio-text-muted)]">
                  <ImageIcon size={19} />
                  {t("task.detail.evidencePhotoPlaceholder")}
                </div>
              )}

              {evidenceAttachmentPreviews.length > 0 && (
                <div className="grid grid-cols-3 gap-2">
                  {evidenceAttachmentPreviews.map((preview) => (
                    <div
                      key={preview.attachment.id}
                      className="group overflow-hidden rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)]"
                    >
                      <button
                        type="button"
                        onClick={() => openPhotoPreview(preview)}
                        className="relative block w-full overflow-hidden text-left"
                      >
                        <img
                          src={preview.objectUrl}
                          alt={preview.attachment.file_name}
                          className="aspect-square w-full object-cover transition group-active:scale-95"
                        />

                        <span className="absolute right-1.5 top-1.5 flex h-7 w-7 items-center justify-center rounded-full bg-slate-950/70 text-white backdrop-blur-sm">
                          <ZoomIn size={14} />
                        </span>
                      </button>

                      <div className="px-2 py-1.5">
                        <p className="truncate text-[0.62rem] font-black text-[var(--missio-text-main)]">
                          {preview.attachment.file_name}
                        </p>
                        <p className="text-[0.58rem] font-bold text-[var(--missio-text-muted)]">
                          {formatFileSize(preview.attachment.file_size, t)}
                        </p>

                        {canDeleteAttachments && (
                          <button
                            type="button"
                            onClick={() => void handleDeleteAttachment(preview.attachment.id)}
                            disabled={deletingAttachmentId === preview.attachment.id}
                            className="mt-1 flex w-full items-center justify-center gap-1 rounded-xl border border-red-200 bg-red-50 px-2 py-1.5 text-[0.62rem] font-black text-red-600 disabled:cursor-not-allowed disabled:opacity-60 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
                          >
                            {deletingAttachmentId === preview.attachment.id ? (
                              <Loader2 className="animate-spin" size={12} />
                            ) : (
                              <Trash2 size={12} />
                            )}
                            {t("task.detail.delete")}
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {canWriteCompletionNote && (
            <div className="mb-4 rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4">
              <div className="mb-3 flex items-start gap-3">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
                  <MessageSquareText size={21} />
                </div>

                <div>
                  <h3 className="text-sm font-black">{t("task.detail.completionNote")}</h3>
                  <p className="mt-1 text-xs font-semibold leading-5 text-[var(--missio-text-muted)]">
                    {t("task.detail.completionNoteDescription")}
                  </p>
                </div>
              </div>

              <textarea
                value={completionNote}
                onChange={(event) => setCompletionNote(event.target.value)}
                placeholder={t("task.detail.completionNotePlaceholder")}
                maxLength={5000}
                className="min-h-24 w-full resize-none rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-3 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
              />

              <div className="mt-2 text-right text-[0.65rem] font-bold text-[var(--missio-text-muted)]">
                {completionNote.length}/5000
              </div>
            </div>
          )}

          <TaskEventTimeline taskId={task.id} refreshVersion={timelineRefreshVersion} />

          <div className="sticky bottom-0 -mx-4 mt-5 border-t border-[var(--missio-border)] bg-[var(--missio-card-bg)]/95 px-4 pb-1 pt-4 backdrop-blur-xl">
            {task.requiresPhoto && !isClosedTask && evidenceAttachmentPreviews.length < 1 && (
              <div className="mb-3 flex items-start gap-2 rounded-2xl border border-amber-200 bg-amber-50 px-3 py-3 text-xs font-black leading-5 text-amber-800 dark:border-amber-900 dark:bg-amber-950/35 dark:text-amber-200">
                <AlertCircle className="mt-0.5 shrink-0" size={17} />
                <span>{t("task.detail.photoRequiredWarning")}</span>
              </div>
            )}

            {actionErrorMessage && (
              <div className="mb-3 flex items-start gap-2 rounded-2xl border border-red-200 bg-red-50 px-3 py-3 text-xs font-black leading-5 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
                <AlertCircle className="mt-0.5 shrink-0" size={17} />
                <span>{actionErrorMessage}</span>
              </div>
            )}

            <button
              type="button"
              onClick={onClose}
              className="mb-3 flex w-full items-center justify-center gap-2 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3 text-sm font-black text-[var(--missio-text-main)] active:scale-[0.99]"
            >
              <ArrowLeft size={18} />
              {t("task.detail.backToList")}
            </button>

            {isClosedTask ? (
              <div className="flex items-center justify-center gap-2 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3 text-sm font-black text-[var(--missio-text-muted)]">
                <CheckCircle2 size={18} />
                {getClosedTaskLabel(task, t)}
              </div>
            ) : (
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
                      onClick={() => fileInputRef.current?.click()}
                      disabled={isBusy || isLoadingAttachments}
                      className={
                        shouldFlashPhotoButton && evidenceAttachmentPreviews.length < 1
                          ? "flex flex-1 animate-pulse items-center justify-center gap-2 rounded-2xl border-2 border-amber-400 bg-amber-50 px-4 py-3 text-sm font-black text-amber-800 ring-4 ring-amber-300/70 shadow-lg shadow-amber-400/30 disabled:cursor-not-allowed disabled:opacity-60 dark:border-amber-500 dark:bg-amber-950/40 dark:text-amber-100 dark:ring-amber-700/60"
                          : "flex flex-1 items-center justify-center gap-2 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3 text-sm font-black disabled:cursor-not-allowed disabled:opacity-60"
                      }
                    >
                      <Camera size={18} />
                      {t("task.detail.addEvidencePhoto")}
                    </button>
                  </>
                )}

                <button
                  type="button"
                  onClick={handleMainAction}
                  disabled={!canUseMainAction || isBusy}
                  className="flex flex-1 items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 py-3 text-sm font-black text-white shadow-lg shadow-teal-500/20 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isBusy ? (
                    <>
                      <Loader2 className="animate-spin" size={18} />
                      {t("task.detail.processing")}
                    </>
                  ) : (
                    <>
                      <PlayCircle size={18} />
                      {getActionButtonLabel(task, t)}
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      </section>

      {selectedPreview && (
        <div className="fixed inset-0 z-50 flex flex-col bg-slate-950 text-white">
          <div className="flex items-start justify-between gap-3 border-b border-white/10 px-4 pb-3 pt-5">
            <div className="min-w-0">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-cyan-300">
                {selectedPreview.attachment.attachment_type === "reference"
                  ? t("task.detail.referencePhoto")
                  : t("task.detail.evidencePhotoPreview")}
              </p>
              <h3 className="mt-1 truncate text-base font-black">
                {selectedPreview.attachment.file_name}
              </h3>
              <p className="mt-1 text-xs font-bold text-slate-400">
                {formatFileSize(selectedPreview.attachment.file_size, t)}
              </p>
            </div>

            <button
              type="button"
              onClick={closePhotoPreview}
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/10 text-white"
              aria-label={t("task.detail.closePhoto")}
            >
              <X size={20} />
            </button>
          </div>

          <div className="flex min-h-0 flex-1 items-center justify-center px-3 py-4">
            <img
              src={selectedPreview.objectUrl}
              alt={selectedPreview.attachment.file_name}
              className="max-h-full max-w-full rounded-2xl object-contain shadow-2xl shadow-black/40"
            />
          </div>

          <div className="border-t border-white/10 bg-slate-950/95 px-4 pb-5 pt-4">
            <button
              type="button"
              onClick={closePhotoPreview}
              className="flex w-full items-center justify-center gap-2 rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-black text-slate-950 active:scale-[0.99]"
            >
              <ArrowLeft size={18} />
              {t("task.detail.returnToDetail")}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
