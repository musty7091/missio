import { useEffect, useMemo, useRef, useState, type ChangeEvent, type ReactNode } from "react"
import { Camera, FileCheck2, ImageIcon, Loader2, MapPin, Mic, Send, Sparkles, Square, Trash2, X } from "lucide-react"

import { useTranslation } from "../../i18n/language"
import { listBusinessUsers, type BusinessUser } from "../../services/businessUserService"
import {
  createExtraTask,
  createRoutineTaskTemplate,
  generateDailyRoutineTasks,
  uploadTaskAttachment,
} from "../../services/taskService"

export type TaskAssignMode = "extra" | "routine"
export type TaskAssignPriority = "low" | "normal" | "high" | "urgent"
type ExtraTaskScheduleMode = "now" | "scheduled"

type TaskAssignSheetProps = {
  businessId: number | null
  isOpen: boolean
  assignableRoles: string[]
  defaultRequiresManagerApproval: boolean
  allowLocationRequirement?: boolean
  onClose: () => void
  onCreated: () => void | Promise<void>
  onSuccess?: (message: string) => void
}

function getLocalTodayDateKey() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, "0")
  const day = String(now.getDate()).padStart(2, "0")

  return `${year}-${month}-${day}`
}

function parseLocalDateTime(dateValue: string, timeValue: string) {
  if (!dateValue || !timeValue) {
    return null
  }

  const [yearText, monthText, dayText] = dateValue.split("-")
  const [hourText, minuteText] = timeValue.split(":")

  const year = Number(yearText)
  const month = Number(monthText)
  const day = Number(dayText)
  const hour = Number(hourText)
  const minute = Number(minuteText)

  if (
    Number.isNaN(year) ||
    Number.isNaN(month) ||
    Number.isNaN(day) ||
    Number.isNaN(hour) ||
    Number.isNaN(minute) ||
    year < 2000 ||
    month < 1 ||
    month > 12 ||
    day < 1 ||
    day > 31 ||
    hour < 0 ||
    hour > 23 ||
    minute < 0 ||
    minute > 59
  ) {
    return null
  }

  const localDate = new Date(year, month - 1, day, hour, minute, 0, 0)

  if (
    localDate.getFullYear() !== year ||
    localDate.getMonth() !== month - 1 ||
    localDate.getDate() !== day ||
    localDate.getHours() !== hour ||
    localDate.getMinutes() !== minute
  ) {
    return null
  }

  return localDate
}

function buildDueAtUtcFromLocalDateTime(dateValue: string, timeValue: string) {
  const localDate = parseLocalDateTime(dateValue, timeValue)

  if (!localDate) {
    return null
  }

  return localDate.toISOString()
}

function isFutureLocalDateTime(dateValue: string, timeValue: string) {
  const localDate = parseLocalDateTime(dateValue, timeValue)

  if (!localDate) {
    return false
  }

  return localDate.getTime() > Date.now()
}

function formatLocalDateLabel(dateValue: string) {
  if (!dateValue) {
    return ""
  }

  const [yearText, monthText, dayText] = dateValue.split("-")
  const year = Number(yearText)
  const month = Number(monthText)
  const day = Number(dayText)

  if (Number.isNaN(year) || Number.isNaN(month) || Number.isNaN(day)) {
    return dateValue
  }

  return `${String(day).padStart(2, "0")}.${String(month).padStart(2, "0")}.${year}`
}

function getSelectedUserLabel(
  users: BusinessUser[],
  selectedUserId: string,
  emptyLabel: string,
) {
  const selectedUser = users.find((user) => String(user.id) === selectedUserId)

  if (!selectedUser) {
    return emptyLabel
  }

  return `${selectedUser.full_name} @${selectedUser.username}`
}

function RequirementToggle({
  label,
  icon,
  isActive,
  isDisabled = false,
  onToggle,
}: {
  label: string
  icon: ReactNode
  isActive: boolean
  isDisabled?: boolean
  onToggle: () => void
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={isDisabled}
      className={
        isActive
          ? "flex min-h-14 flex-col items-center justify-center gap-1 rounded-2xl bg-cyan-500 px-2 py-3 text-xs font-black text-white shadow-lg shadow-cyan-500/20 transition active:scale-95 disabled:cursor-not-allowed disabled:opacity-45"
          : "flex min-h-14 flex-col items-center justify-center gap-1 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-2 py-3 text-xs font-black text-[var(--missio-text-muted)] transition active:scale-95 disabled:cursor-not-allowed disabled:opacity-45"
      }
    >
      {icon}
      {label}
    </button>
  )
}

export function TaskAssignSheet({
  businessId,
  isOpen,
  assignableRoles,
  defaultRequiresManagerApproval,
  allowLocationRequirement = true,
  onClose,
  onCreated,
  onSuccess,
}: TaskAssignSheetProps) {
  const { language } = useTranslation()
  const isTurkish = language === "tr"
  const tx = (tr: string, en: string) => (isTurkish ? tr : en)

  const [users, setUsers] = useState<BusinessUser[]>([])
  const [isLoadingUsers, setIsLoadingUsers] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const [taskMode, setTaskMode] = useState<TaskAssignMode>("extra")
  const [assignedToUserId, setAssignedToUserId] = useState("")
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [extraScheduleMode, setExtraScheduleMode] = useState<ExtraTaskScheduleMode>("now")
  const [dueDate, setDueDate] = useState(getLocalTodayDateKey())
  const [dueTime, setDueTime] = useState("")
  const [priority, setPriority] = useState<TaskAssignPriority>("normal")
  const [requiresPhoto, setRequiresPhoto] = useState(false)
  const [requiresLocation, setRequiresLocation] = useState(false)
  const [requiresManagerApproval, setRequiresManagerApproval] = useState(
    defaultRequiresManagerApproval,
  )
  const [referencePhotoFile, setReferencePhotoFile] = useState<File | null>(null)
  const [referencePhotoPreviewUrl, setReferencePhotoPreviewUrl] = useState<string | null>(null)
  const [voiceNoteBlob, setVoiceNoteBlob] = useState<Blob | null>(null)
  const [voiceNotePreviewUrl, setVoiceNotePreviewUrl] = useState<string | null>(null)
  const [voiceRecordingState, setVoiceRecordingState] = useState<"idle" | "recording" | "recorded">("idle")
  const [voiceElapsedSeconds, setVoiceElapsedSeconds] = useState(0)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const voiceStreamRef = useRef<MediaStream | null>(null)
  const voiceChunksRef = useRef<BlobPart[]>([])
  const voiceTimerRef = useRef<number | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const assignableUsers = useMemo(
    () =>
      users.filter(
        (user) => user.is_active && assignableRoles.includes(user.role),
      ),
    [assignableRoles, users],
  )

  const selectedUserLabel = getSelectedUserLabel(
    assignableUsers,
    assignedToUserId,
    tx("Personel seçilmedi", "No staff selected"),
  )

  const selectedTaskModeLabel =
    taskMode === "routine"
      ? tx("Rutin görev", "Routine task")
      : tx("Tek seferlik görev", "One-time task")

  const selectedDueTimeLabel =
    taskMode === "routine"
      ? dueTime || tx("Saat belirtilmedi", "No time set")
      : extraScheduleMode === "scheduled"
        ? dueDate && dueTime
          ? `${formatLocalDateLabel(dueDate)} ${dueTime}`
          : tx("Plan zamanı eksik", "Schedule time missing")
        : tx("Hemen gönder", "Send now")

  const requirementSummary =
    [
      requiresPhoto ? tx("Fotoğraf", "Photo") : null,
      requiresLocation ? tx("Konum", "Location") : null,
      requiresManagerApproval ? tx("Yönetici onayı", "Manager approval") : null,
      referencePhotoFile ? tx("Referans fotoğraf", "Reference photo") : null,
      voiceNoteBlob ? tx("Sesli not", "Voice note") : null,
    ]
      .filter(Boolean)
      .join(" + ") || tx("Ek şart yok", "No extra requirement")

  function resetForm() {
    setTaskMode("extra")
    setAssignedToUserId("")
    setTitle("")
    setDescription("")
    setExtraScheduleMode("now")
    setDueDate(getLocalTodayDateKey())
    setDueTime("")
    setPriority("normal")
    setRequiresPhoto(false)
    setRequiresLocation(false)
    setRequiresManagerApproval(defaultRequiresManagerApproval)
    setReferencePhotoFile(null)
    setReferencePhotoPreviewUrl((currentUrl) => {
      if (currentUrl) {
        URL.revokeObjectURL(currentUrl)
      }

      return null
    })
    setVoiceNoteBlob(null)
    setVoiceNotePreviewUrl((currentUrl) => {
      if (currentUrl) {
        URL.revokeObjectURL(currentUrl)
      }

      return null
    })
    setVoiceRecordingState("idle")
    setVoiceElapsedSeconds(0)
    clearVoiceRecordingTimer()
    stopVoiceStream()
    setErrorMessage(null)
  }

  async function loadUsers() {
    if (!businessId) {
      setUsers([])
      return
    }

    setIsLoadingUsers(true)
    setErrorMessage(null)

    try {
      const response = await listBusinessUsers(businessId)
      setUsers(response)
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage(tx("Personel listesi alınamadı.", "Staff list could not be loaded."))
      }
    } finally {
      setIsLoadingUsers(false)
    }
  }

  useEffect(() => {
    if (!isOpen) {
      return
    }

    void loadUsers()
  }, [businessId, isOpen])

  useEffect(() => {
    if (!isOpen) {
      return
    }

    if (assignableUsers.length === 0) {
      setAssignedToUserId("")
      return
    }

    const selectedUserExists = assignableUsers.some(
      (user) => String(user.id) === assignedToUserId,
    )

    if (!selectedUserExists) {
      setAssignedToUserId(String(assignableUsers[0].id))
    }
  }, [assignableUsers, assignedToUserId, isOpen])

  function clearVoiceRecordingTimer() {
    if (voiceTimerRef.current !== null) {
      window.clearInterval(voiceTimerRef.current)
      voiceTimerRef.current = null
    }
  }

  function stopVoiceStream() {
    if (voiceStreamRef.current) {
      voiceStreamRef.current.getTracks().forEach((track) => track.stop())
      voiceStreamRef.current = null
    }
  }

  function formatVoiceSeconds(seconds: number) {
    return `00:${String(seconds).padStart(2, "0")}`
  }

  function getSupportedVoiceMimeType() {
    if (typeof MediaRecorder === "undefined") {
      return ""
    }

    const candidates = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/mp4",
    ]

    return candidates.find((candidate) => MediaRecorder.isTypeSupported(candidate)) ?? ""
  }

  useEffect(() => {
    if (!referencePhotoFile) {
      setReferencePhotoPreviewUrl((currentUrl) => {
        if (currentUrl) {
          URL.revokeObjectURL(currentUrl)
        }

        return null
      })
      return
    }

    const objectUrl = URL.createObjectURL(referencePhotoFile)
    setReferencePhotoPreviewUrl(objectUrl)

    return () => {
      URL.revokeObjectURL(objectUrl)
    }
  }, [referencePhotoFile])

  useEffect(() => {
    if (!voiceNoteBlob) {
      setVoiceNotePreviewUrl((currentUrl) => {
        if (currentUrl) {
          URL.revokeObjectURL(currentUrl)
        }

        return null
      })
      return
    }

    const objectUrl = URL.createObjectURL(voiceNoteBlob)
    setVoiceNotePreviewUrl(objectUrl)

    return () => {
      URL.revokeObjectURL(objectUrl)
    }
  }, [voiceNoteBlob])

  useEffect(() => {
    if (!isOpen) {
      return
    }

    const scrollY = window.scrollY
    const originalOverflow = document.body.style.overflow
    const originalPosition = document.body.style.position
    const originalTop = document.body.style.top
    const originalLeft = document.body.style.left
    const originalRight = document.body.style.right
    const originalWidth = document.body.style.width

    document.body.style.overflow = "hidden"
    document.body.style.position = "fixed"
    document.body.style.top = `-${scrollY}px`
    document.body.style.left = "0"
    document.body.style.right = "0"
    document.body.style.width = "100%"

    return () => {
      document.body.style.overflow = originalOverflow
      document.body.style.position = originalPosition
      document.body.style.top = originalTop
      document.body.style.left = originalLeft
      document.body.style.right = originalRight
      document.body.style.width = originalWidth
      window.scrollTo(0, scrollY)
    }
  }, [isOpen])

  async function startVoiceRecording() {
    if (taskMode === "routine") {
      setErrorMessage(tx(
        "Sesli görev notu şimdilik sadece tek seferlik görevlerde destekleniyor.",
        "Voice task notes are currently supported only for one-time tasks.",
      ))
      return
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      setErrorMessage(tx(
        "Bu tarayıcı ses kaydını desteklemiyor.",
        "This browser does not support voice recording.",
      ))
      return
    }

    if (typeof MediaRecorder === "undefined") {
      setErrorMessage(tx(
        "Bu tarayıcı ses kaydını desteklemiyor.",
        "This browser does not support voice recording.",
      ))
      return
    }

    try {
      setErrorMessage(null)
      setVoiceNoteBlob(null)
      setVoiceElapsedSeconds(0)
      voiceChunksRef.current = []

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      voiceStreamRef.current = stream

      const mimeType = getSupportedVoiceMimeType()
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream)

      mediaRecorderRef.current = recorder

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          voiceChunksRef.current.push(event.data)
        }
      }

      recorder.onstop = () => {
        clearVoiceRecordingTimer()
        stopVoiceStream()

        const recordedBlob = new Blob(voiceChunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        })

        if (recordedBlob.size <= 0) {
          setVoiceRecordingState("idle")
          setErrorMessage(tx(
            "Ses kaydı alınamadı. Lütfen tekrar dene.",
            "Voice recording could not be captured. Please try again.",
          ))
          return
        }

        setVoiceNoteBlob(recordedBlob)
        setVoiceRecordingState("recorded")
      }

      recorder.start()
      setVoiceRecordingState("recording")

      voiceTimerRef.current = window.setInterval(() => {
        setVoiceElapsedSeconds((currentSeconds) => {
          const nextSeconds = currentSeconds + 1

          if (nextSeconds >= 30) {
            stopVoiceRecording()
            return 30
          }

          return nextSeconds
        })
      }, 1000)
    } catch (error) {
      clearVoiceRecordingTimer()
      stopVoiceStream()
      setVoiceRecordingState("idle")

      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage(tx(
          "Ses kaydı başlatılamadı.",
          "Voice recording could not be started.",
        ))
      }
    }
  }

  function stopVoiceRecording() {
    const recorder = mediaRecorderRef.current

    if (recorder && recorder.state === "recording") {
      recorder.stop()
      return
    }

    clearVoiceRecordingTimer()
    stopVoiceStream()
    setVoiceRecordingState("idle")
  }

  function removeVoiceNote() {
    if (voiceRecordingState === "recording") {
      stopVoiceRecording()
    }

    setVoiceNoteBlob(null)
    setVoiceRecordingState("idle")
    setVoiceElapsedSeconds(0)
  }

  function handleReferencePhotoChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null

    if (!file) {
      setReferencePhotoFile(null)
      return
    }

    if (!file.type.startsWith("image/")) {
      setErrorMessage(tx(
        "Referans fotoğrafı için sadece görsel dosyası seçebilirsin.",
        "Only image files can be selected as reference photos.",
      ))
      event.target.value = ""
      setReferencePhotoFile(null)
      return
    }

    setErrorMessage(null)
    setReferencePhotoFile(file)
  }

  function removeReferencePhoto() {
    setReferencePhotoFile(null)
  }

  function closeSheet() {
    if (isSaving) {
      return
    }

    resetForm()
    onClose()
  }

  async function handleCreateTask() {
    const selectedUserId = Number(assignedToUserId)
    const trimmedTitle = title.trim()
    const trimmedDescription = description.trim()

    if (!businessId) {
      setErrorMessage(tx(
        "Bu kullanıcı için işletme bilgisi bulunamadı.",
        "Business information could not be found for this user.",
      ))
      return
    }

    if (!selectedUserId) {
      setErrorMessage(tx(
        "Görev atanacak personeli seçmelisin.",
        "You must select a staff member for this task.",
      ))
      return
    }

    if (trimmedTitle.length < 2) {
      setErrorMessage(tx(
        "Görev başlığı en az 2 karakter olmalıdır.",
        "Task title must be at least 2 characters.",
      ))
      return
    }

    if (taskMode === "routine" && (referencePhotoFile || voiceNoteBlob)) {
      setErrorMessage(tx(
        "Referans fotoğrafı ve sesli not şimdilik sadece tek seferlik görevlerde destekleniyor.",
        "Reference photos and voice notes are currently supported only for one-time tasks.",
      ))
      return
    }

    if (voiceRecordingState === "recording") {
      setErrorMessage(tx(
        "Görevi kaydetmeden önce ses kaydını durdurmalısın.",
        "You must stop the voice recording before saving the task.",
      ))
      return
    }

    if (taskMode === "extra" && extraScheduleMode === "scheduled") {
      if (!dueDate || !dueTime) {
        setErrorMessage(tx(
          "Planlı görev için tarih ve saat seçmelisin.",
          "You must select a date and time for scheduled tasks.",
        ))
        return
      }

      if (!buildDueAtUtcFromLocalDateTime(dueDate, dueTime)) {
        setErrorMessage(tx(
          "Planlı görev tarihi veya saati geçersiz.",
          "Scheduled task date or time is invalid.",
        ))
        return
      }

      if (!isFutureLocalDateTime(dueDate, dueTime)) {
        setErrorMessage(tx(
          "Planlı görev zamanı gelecekte olmalıdır. Hemen göndermek için 'Hemen gönder' seçeneğini kullan.",
          "Scheduled task time must be in the future. Use 'Send now' to notify immediately.",
        ))
        return
      }
    }

    setIsSaving(true)
    setErrorMessage(null)

    try {
      if (taskMode === "routine") {
        await createRoutineTaskTemplate({
          assigned_to_user_id: selectedUserId,
          title: trimmedTitle,
          description: trimmedDescription || null,
          category_id: null,
          recurrence_type: "daily",
          default_priority: priority,
          default_due_time_local: dueTime || null,
          default_due_offset_minutes: null,
          requires_photo: requiresPhoto,
          requires_location: requiresLocation,
          requires_manager_approval: requiresManagerApproval,
        })

        await generateDailyRoutineTasks({
          task_date: getLocalTodayDateKey(),
          assigned_to_user_id: selectedUserId,
        })

        onSuccess?.(tx(
          "Rutin görev oluşturuldu ve bugünün görevlerine işlendi.",
          "Routine task was created and added to today's tasks.",
        ))
      } else {
        const createdTaskResponse = await createExtraTask({
          assigned_to_user_id: selectedUserId,
          title: trimmedTitle,
          description: trimmedDescription || null,
          category_id: null,
          priority,
          due_at_utc:
            extraScheduleMode === "scheduled"
              ? buildDueAtUtcFromLocalDateTime(dueDate, dueTime)
              : null,
          requires_photo: requiresPhoto,
          requires_location: requiresLocation,
          requires_manager_approval: requiresManagerApproval,
        })

        if (referencePhotoFile) {
          await uploadTaskAttachment(createdTaskResponse.task.id, {
            file: referencePhotoFile,
            attachmentType: "reference",
          })
        }

        if (voiceNoteBlob) {
          const voiceNoteFile = new File(
            [voiceNoteBlob],
            `missio-voice-note-${Date.now()}.webm`,
            {
              type: voiceNoteBlob.type || "audio/webm",
            },
          )

          await uploadTaskAttachment(createdTaskResponse.task.id, {
            file: voiceNoteFile,
            attachmentType: "voice_note",
          })
        }

        if (extraScheduleMode === "scheduled") {
          onSuccess?.(tx(
            "Tek seferlik görev planlandı. Bildirim seçilen tarih ve saatte personele ulaşacak.",
            "One-time task was scheduled. The notification will reach the staff member at the selected date and time.",
          ))
        } else {
          onSuccess?.(
            referencePhotoFile || voiceNoteBlob
              ? tx(
                  "Tek seferlik görev medya ekleriyle personele atandı.",
                  "One-time task was assigned to staff with media attachments.",
                )
              : tx(
                  "Tek seferlik görev personele atandı.",
                  "One-time task was assigned to staff.",
                ),
          )
        }
      }

      resetForm()
      await onCreated()
      onClose()
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage(tx("Görev oluşturulamadı.", "Task could not be created."))
      }
    } finally {
      setIsSaving(false)
    }
  }

  if (!isOpen) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center overflow-hidden overscroll-none bg-slate-950/55 px-3 pb-[max(1rem,env(safe-area-inset-bottom))] pt-[max(7.5rem,env(safe-area-inset-top))] backdrop-blur-sm">
      <div className="max-h-[calc(100dvh-9rem)] w-full max-w-[430px] overflow-y-auto overscroll-contain rounded-[2rem] bg-[var(--missio-page-bg)] shadow-2xl">
        <div className="sticky top-0 z-10 border-b border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--missio-text-muted)]">
                {tx("Yeni görev", "New task")}
              </p>

              <h3 className="mt-1 text-xl font-black text-[var(--missio-text-main)]">
                {taskMode === "extra"
                  ? tx("Tek seferlik görev ata", "Assign one-time task")
                  : tx("Rutin görev oluştur", "Create routine task")}
              </h3>
            </div>

            <button
              type="button"
              onClick={closeSheet}
              disabled={isSaving}
              className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[var(--missio-card-bg)] text-[var(--missio-text-main)] shadow-sm disabled:opacity-60"
              aria-label={tx("Kapat", "Close")}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        <div className="space-y-4 p-4">
          {errorMessage && (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-3 text-sm font-black text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
              {errorMessage}
            </div>
          )}

          <section>
            <p className="mb-2 text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
              {tx("Görev tipi", "Task type")}
            </p>

            <div className="grid grid-cols-2 gap-2 rounded-2xl bg-[var(--missio-card-bg)] p-1">
              <button
                type="button"
                onClick={() => setTaskMode("extra")}
                className={
                  taskMode === "extra"
                    ? "min-h-12 rounded-2xl bg-cyan-500 px-3 text-sm font-black text-white shadow-lg shadow-cyan-500/20"
                    : "min-h-12 rounded-2xl px-3 text-sm font-black text-[var(--missio-text-muted)]"
                }
              >
                {tx("Tek seferlik", "One-time")}
              </button>

              <button
                type="button"
                onClick={() => {
                  setTaskMode("routine")
                  setExtraScheduleMode("now")
                  setDueDate(getLocalTodayDateKey())
                }}
                className={
                  taskMode === "routine"
                    ? "min-h-12 rounded-2xl bg-cyan-500 px-3 text-sm font-black text-white shadow-lg shadow-cyan-500/20"
                    : "min-h-12 rounded-2xl px-3 text-sm font-black text-[var(--missio-text-muted)]"
                }
              >
                {tx("Rutin", "Routine")}
              </button>
            </div>

            <p className="mt-2 text-xs font-bold leading-5 text-[var(--missio-text-muted)]">
              {taskMode === "extra"
                ? tx(
                    "Tek seferlik görev hemen gönderilebilir veya seçilen ileri tarih ve saate planlanabilir.",
                    "One-time task can be sent now or scheduled for a future date and time.",
                  )
                : tx(
                    "Rutin görev şablonu oluşturulur ve bugüne de işlenir.",
                    "A routine task template is created and also added to today.",
                  )}
            </p>
          </section>

          <section>
            <div className="mb-2 flex items-center justify-between gap-3">
              <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                {tx("Personel", "Staff")}
              </p>

              <span className="rounded-full bg-cyan-100 px-2.5 py-1 text-[0.65rem] font-black text-cyan-800 dark:bg-cyan-950 dark:text-cyan-200">
                {isLoadingUsers
                  ? tx("Yükleniyor", "Loading")
                  : tx(`${assignableUsers.length} aktif`, `${assignableUsers.length} active`)}
              </span>
            </div>

            <select
              value={assignedToUserId}
              onChange={(event) => setAssignedToUserId(event.target.value)}
              disabled={isLoadingUsers}
              className="min-h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400 disabled:opacity-60"
            >
              {assignableUsers.length === 0 ? (
                <option value="">
                  {tx("Aktif personel yok", "No active staff")}
                </option>
              ) : (
                assignableUsers.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.full_name} (@{user.username})
                  </option>
                ))
              )}
            </select>
          </section>

          <label className="block">
            <span className="mb-1.5 block text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
              {tx("Görev başlığı", "Task title")}
            </span>
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder={tx("Örn: Raf düzeni kontrol edilsin", "Example: Check shelf order")}
              className="min-h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
            />
          </label>

          <label className="block">
            <span className="mb-1.5 block text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
              {tx("Açıklama", "Description")}
            </span>
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder={tx(
                "Personelin görevi nasıl yapacağını açıkla...",
                "Explain how the staff member should complete the task...",
              )}
              className="min-h-24 w-full resize-none rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-3 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
            />
          </label>

          {taskMode === "extra" ? (
            <section className="rounded-[1.4rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3">
              <p className="mb-2 text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                {tx("Gönderim zamanı", "Send time")}
              </p>

              <div className="grid grid-cols-2 gap-2 rounded-2xl bg-[var(--missio-page-bg)] p-1">
                <button
                  type="button"
                  onClick={() => setExtraScheduleMode("now")}
                  className={
                    extraScheduleMode === "now"
                      ? "min-h-12 rounded-2xl bg-cyan-500 px-3 text-sm font-black text-white shadow-lg shadow-cyan-500/20"
                      : "min-h-12 rounded-2xl px-3 text-sm font-black text-[var(--missio-text-muted)]"
                  }
                >
                  {tx("Hemen gönder", "Send now")}
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setExtraScheduleMode("scheduled")
                    setDueDate((currentDate) => currentDate || getLocalTodayDateKey())
                  }}
                  className={
                    extraScheduleMode === "scheduled"
                      ? "min-h-12 rounded-2xl bg-cyan-500 px-3 text-sm font-black text-white shadow-lg shadow-cyan-500/20"
                      : "min-h-12 rounded-2xl px-3 text-sm font-black text-[var(--missio-text-muted)]"
                  }
                >
                  {tx("Planlı gönder", "Schedule")}
                </button>
              </div>

              {extraScheduleMode === "scheduled" ? (
                <div className="mt-3 grid grid-cols-2 gap-2">
                  <label className="block">
                    <span className="mb-1.5 block text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                      {tx("Tarih", "Date")}
                    </span>
                    <input
                      type="date"
                      value={dueDate}
                      min={getLocalTodayDateKey()}
                      onChange={(event) => setDueDate(event.target.value)}
                      className="min-h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
                    />
                  </label>

                  <label className="block">
                    <span className="mb-1.5 block text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                      {tx("Saat", "Time")}
                    </span>
                    <input
                      type="time"
                      value={dueTime}
                      onChange={(event) => setDueTime(event.target.value)}
                      className="min-h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
                    />
                  </label>
                </div>
              ) : (
                <p className="mt-3 rounded-2xl bg-cyan-50 px-3 py-3 text-xs font-black leading-5 text-cyan-800 dark:bg-cyan-950/35 dark:text-cyan-100">
                  {tx(
                    "Görev kaydedildiği anda personele bildirim gider.",
                    "The staff member will be notified as soon as the task is saved.",
                  )}
                </p>
              )}
            </section>
          ) : (
            <label className="block">
              <span className="mb-1.5 block text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                {tx("Her gün saat", "Daily time")}
              </span>
              <input
                type="time"
                value={dueTime}
                onChange={(event) => setDueTime(event.target.value)}
                className="min-h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
              />
            </label>
          )}

          <label className="block">
            <span className="mb-1.5 block text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
              {tx("Öncelik", "Priority")}
            </span>
            <select
              value={priority}
              onChange={(event) => setPriority(event.target.value as TaskAssignPriority)}
              className="min-h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
            >
              <option value="low">{tx("Düşük", "Low")}</option>
              <option value="normal">{tx("Normal", "Normal")}</option>
              <option value="high">{tx("Yüksek", "High")}</option>
              <option value="urgent">{tx("Acil", "Urgent")}</option>
            </select>
          </label>

          <section>
            <p className="mb-2 text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
              {tx("Görev şartları", "Task requirements")}
            </p>

            <div className="grid grid-cols-3 gap-2">
              <RequirementToggle
                label={tx("Fotoğraf", "Photo")}
                icon={<Camera size={18} />}
                isActive={requiresPhoto}
                onToggle={() => setRequiresPhoto((value) => !value)}
              />

              <RequirementToggle
                label={tx("Konum", "Location")}
                icon={<MapPin size={18} />}
                isActive={requiresLocation}
                isDisabled={!allowLocationRequirement}
                onToggle={() => {
                  if (allowLocationRequirement) {
                    setRequiresLocation((value) => !value)
                  }
                }}
              />

              <RequirementToggle
                label={tx("Onay", "Approval")}
                icon={<FileCheck2 size={18} />}
                isActive={requiresManagerApproval}
                onToggle={() => setRequiresManagerApproval((value) => !value)}
              />
            </div>
          </section>

          <section className="rounded-[1.4rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3">
            <div className="mb-3 flex items-start gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
                <ImageIcon size={21} />
              </div>

              <div className="min-w-0 flex-1">
                <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                  {tx("Referans fotoğrafı", "Reference photo")}
                </p>
                <p className="mt-1 text-xs font-semibold leading-5 text-[var(--missio-text-muted)]">
                  {tx(
                    "Personel görevi açınca bu görseli yapılacak işin örneği olarak görecek.",
                    "The staff member will see this image as an example of the task.",
                  )}
                </p>
              </div>
            </div>

            {taskMode === "routine" ? (
              <div className="rounded-2xl border border-amber-200 bg-amber-50 px-3 py-3 text-xs font-black leading-5 text-amber-800 dark:border-amber-900 dark:bg-amber-950/35 dark:text-amber-200">
                {tx(
                  "Referans fotoğrafı şimdilik sadece tek seferlik görevlerde kullanılabilir.",
                  "Reference photos are currently available only for one-time tasks.",
                )}
              </div>
            ) : referencePhotoPreviewUrl ? (
              <div className="overflow-hidden rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)]">
                <img
                  src={referencePhotoPreviewUrl}
                  alt={tx("Referans fotoğrafı önizleme", "Reference photo preview")}
                  className="max-h-56 w-full object-cover"
                />

                <div className="flex items-center justify-between gap-3 px-3 py-2">
                  <p className="min-w-0 truncate text-xs font-black text-[var(--missio-text-main)]">
                    {referencePhotoFile?.name}
                  </p>

                  <button
                    type="button"
                    onClick={removeReferencePhoto}
                    disabled={isSaving}
                    className="shrink-0 rounded-xl border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-black text-red-600 disabled:opacity-60 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
                  >
                    {tx("Kaldır", "Remove")}
                  </button>
                </div>
              </div>
            ) : (
              <label className="flex min-h-24 cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-4 text-center text-sm font-black text-[var(--missio-text-muted)] active:scale-[0.99]">
                <ImageIcon size={24} />
                {tx("Referans fotoğrafı seç", "Select reference photo")}
                <input
                  type="file"
                  accept="image/*"
                  className="hidden"
                  disabled={isSaving}
                  onChange={handleReferencePhotoChange}
                />
              </label>
            )}
          </section>

          <section className="rounded-[1.4rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3">
            <div className="mb-3 flex items-start gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
                <Mic size={21} />
              </div>

              <div className="min-w-0 flex-1">
                <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                  {tx("Sesli görev notu", "Voice task note")}
                </p>
                <p className="mt-1 text-xs font-semibold leading-5 text-[var(--missio-text-muted)]">
                  {tx(
                    "En fazla 30 saniyelik kısa bir sesli açıklama kaydedebilirsin.",
                    "You can record a short voice note up to 30 seconds.",
                  )}
                </p>
              </div>
            </div>

            {taskMode === "routine" ? (
              <div className="rounded-2xl border border-amber-200 bg-amber-50 px-3 py-3 text-xs font-black leading-5 text-amber-800 dark:border-amber-900 dark:bg-amber-950/35 dark:text-amber-200">
                {tx(
                  "Sesli görev notu şimdilik sadece tek seferlik görevlerde kullanılabilir.",
                  "Voice task notes are currently available only for one-time tasks.",
                )}
              </div>
            ) : (
              <div className="rounded-[1.35rem] border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-3">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-black text-[var(--missio-text-main)]">
                      {voiceRecordingState === "recording"
                        ? tx("Kayıt yapılıyor...", "Recording...")
                        : voiceRecordingState === "recorded"
                          ? tx("Sesli not hazır", "Voice note ready")
                          : tx("Kayıt hazır", "Ready to record")}
                    </p>
                    <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
                      {formatVoiceSeconds(voiceElapsedSeconds)} / 00:30
                    </p>
                  </div>

                  <div
                    className={
                      voiceRecordingState === "recording"
                        ? "flex h-12 w-12 items-center justify-center rounded-full bg-red-500 text-white shadow-lg shadow-red-500/30 animate-pulse"
                        : "flex h-12 w-12 items-center justify-center rounded-full bg-cyan-500 text-white shadow-lg shadow-cyan-500/20"
                    }
                  >
                    <Mic size={22} />
                  </div>
                </div>

                <div className="h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                  <div
                    className={
                      voiceRecordingState === "recording"
                        ? "h-full rounded-full bg-red-500 transition-all"
                        : "h-full rounded-full bg-cyan-500 transition-all"
                    }
                    style={{ width: `${Math.min(100, (voiceElapsedSeconds / 30) * 100)}%` }}
                  />
                </div>

                {voiceNotePreviewUrl && (
                  <audio
                    controls
                    src={voiceNotePreviewUrl}
                    className="mt-3 w-full"
                  />
                )}

                <div className="mt-3 flex gap-2">
                  {voiceRecordingState === "recording" ? (
                    <button
                      type="button"
                      onClick={stopVoiceRecording}
                      disabled={isSaving}
                      className="flex min-h-12 flex-1 items-center justify-center gap-2 rounded-2xl bg-red-500 px-4 py-3 text-sm font-black text-white shadow-lg shadow-red-500/20 disabled:opacity-60"
                    >
                      <Square size={17} />
                      {tx("Kaydı durdur", "Stop recording")}
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => void startVoiceRecording()}
                      disabled={isSaving}
                      className="flex min-h-12 flex-1 items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 py-3 text-sm font-black text-white shadow-lg shadow-teal-500/20 disabled:opacity-60"
                    >
                      <Mic size={17} />
                      {voiceNoteBlob
                        ? tx("Yeniden kaydet", "Record again")
                        : tx("Kayıt başlat", "Start recording")}
                    </button>
                  )}

                  {voiceNoteBlob && (
                    <button
                      type="button"
                      onClick={removeVoiceNote}
                      disabled={isSaving}
                      className="flex min-h-12 items-center justify-center rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-black text-red-600 disabled:opacity-60 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
                      aria-label={tx("Sesli notu sil", "Delete voice note")}
                    >
                      <Trash2 size={18} />
                    </button>
                  )}
                </div>
              </div>
            )}
          </section>

          <section className="rounded-[1.4rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                  {tx("Kaydetmeden önce", "Before saving")}
                </p>

                <h4 className="mt-1 text-sm font-black text-[var(--missio-text-main)]">
                  {tx("Görev özeti", "Task summary")}
                </h4>
              </div>

              <span className="rounded-full bg-cyan-100 px-2.5 py-1 text-[0.65rem] font-black text-cyan-800 dark:bg-cyan-950 dark:text-cyan-200">
                {selectedTaskModeLabel}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs font-bold">
              <div className="rounded-2xl bg-white/60 px-3 py-2 dark:bg-white/5">
                <p className="text-[0.62rem] font-black uppercase tracking-wide text-[var(--missio-text-muted)]">
                  {tx("Personel", "Staff")}
                </p>
                <p className="mt-1 truncate text-[var(--missio-text-main)]">
                  {selectedUserLabel}
                </p>
              </div>

              <div className="rounded-2xl bg-white/60 px-3 py-2 dark:bg-white/5">
                <p className="text-[0.62rem] font-black uppercase tracking-wide text-[var(--missio-text-muted)]">
                  {taskMode === "routine" ? tx("Saat", "Time") : tx("Gönderim", "Send time")}
                </p>
                <p className="mt-1 truncate text-[var(--missio-text-main)]">
                  {selectedDueTimeLabel}
                </p>
              </div>

              <div className="col-span-2 rounded-2xl bg-white/60 px-3 py-2 dark:bg-white/5">
                <p className="text-[0.62rem] font-black uppercase tracking-wide text-[var(--missio-text-muted)]">
                  {tx("Şartlar", "Requirements")}
                </p>
                <p className="mt-1 text-[var(--missio-text-main)]">
                  {requirementSummary}
                </p>
              </div>
            </div>
          </section>

          <button
            type="button"
            onClick={() => void handleCreateTask()}
            disabled={isSaving}
            className="flex min-h-13 w-full items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 py-3 text-sm font-black text-white shadow-lg shadow-teal-500/20 transition active:scale-95 disabled:cursor-wait disabled:opacity-60"
          >
            {isSaving ? (
              <Loader2 className="animate-spin" size={18} />
            ) : taskMode === "extra" ? (
              <Send size={18} />
            ) : (
              <Sparkles size={18} />
            )}

            {taskMode === "extra"
              ? tx("Tek seferlik görevi ata", "Assign one-time task")
              : tx("Rutin görevi oluştur", "Create routine task")}
          </button>
        </div>
      </div>
    </div>
  )
}