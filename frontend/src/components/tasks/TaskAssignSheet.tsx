import { useEffect, useMemo, useState, type ReactNode } from "react"
import { Camera, FileCheck2, Loader2, MapPin, Send, Sparkles, X } from "lucide-react"

import { listBusinessUsers, type BusinessUser } from "../../services/businessUserService"
import {
  createExtraTask,
  createRoutineTaskTemplate,
  generateDailyRoutineTasks,
} from "../../services/taskService"

export type TaskAssignMode = "extra" | "routine"
export type TaskAssignPriority = "low" | "normal" | "high" | "urgent"

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

function buildDueAtUtcFromLocalTime(timeValue: string) {
  if (!timeValue) {
    return null
  }

  const [hourText, minuteText] = timeValue.split(":")
  const hour = Number(hourText)
  const minute = Number(minuteText)

  if (
    Number.isNaN(hour) ||
    Number.isNaN(minute) ||
    hour < 0 ||
    hour > 23 ||
    minute < 0 ||
    minute > 59
  ) {
    return null
  }

  const now = new Date()
  const dueDate = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
    hour,
    minute,
    0,
    0,
  )

  return dueDate.toISOString()
}

function getSelectedUserLabel(users: BusinessUser[], selectedUserId: string) {
  const selectedUser = users.find((user) => String(user.id) === selectedUserId)

  if (!selectedUser) {
    return "Personel seçilmedi"
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
  const [users, setUsers] = useState<BusinessUser[]>([])
  const [isLoadingUsers, setIsLoadingUsers] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const [taskMode, setTaskMode] = useState<TaskAssignMode>("extra")
  const [assignedToUserId, setAssignedToUserId] = useState("")
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [dueTime, setDueTime] = useState("")
  const [priority, setPriority] = useState<TaskAssignPriority>("normal")
  const [requiresPhoto, setRequiresPhoto] = useState(false)
  const [requiresLocation, setRequiresLocation] = useState(false)
  const [requiresManagerApproval, setRequiresManagerApproval] = useState(
    defaultRequiresManagerApproval,
  )
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const assignableUsers = useMemo(
    () =>
      users.filter(
        (user) => user.is_active && assignableRoles.includes(user.role),
      ),
    [assignableRoles, users],
  )

  const selectedUserLabel = getSelectedUserLabel(assignableUsers, assignedToUserId)
  const selectedTaskModeLabel = taskMode === "routine" ? "Rutin görev" : "Ekstra görev"
  const selectedDueTimeLabel = dueTime || "Saat belirtilmedi"
  const requirementSummary =
    [
      requiresPhoto ? "Fotoğraf" : null,
      requiresLocation ? "Konum" : null,
      requiresManagerApproval ? "Yönetici onayı" : null,
    ]
      .filter(Boolean)
      .join(" + ") || "Ek şart yok"

  function resetForm() {
    setTaskMode("extra")
    setAssignedToUserId("")
    setTitle("")
    setDescription("")
    setDueTime("")
    setPriority("normal")
    setRequiresPhoto(false)
    setRequiresLocation(false)
    setRequiresManagerApproval(defaultRequiresManagerApproval)
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
        setErrorMessage("Personel listesi alınamadı.")
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
      setErrorMessage("Bu kullanıcı için işletme bilgisi bulunamadı.")
      return
    }

    if (!selectedUserId) {
      setErrorMessage("Görev atanacak personeli seçmelisin.")
      return
    }

    if (trimmedTitle.length < 2) {
      setErrorMessage("Görev başlığı en az 2 karakter olmalıdır.")
      return
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

        onSuccess?.("Rutin görev oluşturuldu ve bugünün görevlerine işlendi.")
      } else {
        await createExtraTask({
          assigned_to_user_id: selectedUserId,
          title: trimmedTitle,
          description: trimmedDescription || null,
          category_id: null,
          priority,
          due_at_utc: buildDueAtUtcFromLocalTime(dueTime),
          requires_photo: requiresPhoto,
          requires_location: requiresLocation,
          requires_manager_approval: requiresManagerApproval,
        })

        onSuccess?.("Ekstra görev personele atandı.")
      }

      resetForm()
      await onCreated()
      onClose()
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Görev oluşturulamadı.")
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
                Yeni görev
              </p>

              <h3 className="mt-1 text-xl font-black text-[var(--missio-text-main)]">
                {taskMode === "extra" ? "Ekstra görev ata" : "Rutin görev oluştur"}
              </h3>
            </div>

            <button
              type="button"
              onClick={closeSheet}
              disabled={isSaving}
              className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[var(--missio-card-bg)] text-[var(--missio-text-main)] shadow-sm disabled:opacity-60"
              aria-label="Kapat"
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
              Görev tipi
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
                Ekstra
              </button>

              <button
                type="button"
                onClick={() => setTaskMode("routine")}
                className={
                  taskMode === "routine"
                    ? "min-h-12 rounded-2xl bg-cyan-500 px-3 text-sm font-black text-white shadow-lg shadow-cyan-500/20"
                    : "min-h-12 rounded-2xl px-3 text-sm font-black text-[var(--missio-text-muted)]"
                }
              >
                Rutin
              </button>
            </div>

            <p className="mt-2 text-xs font-bold leading-5 text-[var(--missio-text-muted)]">
              {taskMode === "extra"
                ? "Ekstra görev bugüne özel tek seferlik olarak atanır."
                : "Rutin görev şablonu oluşturulur ve bugüne de işlenir."}
            </p>
          </section>

          <section>
            <div className="mb-2 flex items-center justify-between gap-3">
              <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                Personel
              </p>

              <span className="rounded-full bg-cyan-100 px-2.5 py-1 text-[0.65rem] font-black text-cyan-800 dark:bg-cyan-950 dark:text-cyan-200">
                {isLoadingUsers ? "Yükleniyor" : `${assignableUsers.length} aktif`}
              </span>
            </div>

            <select
              value={assignedToUserId}
              onChange={(event) => setAssignedToUserId(event.target.value)}
              disabled={isLoadingUsers}
              className="min-h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400 disabled:opacity-60"
            >
              {assignableUsers.length === 0 ? (
                <option value="">Aktif personel yok</option>
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
              Görev başlığı
            </span>
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Örn: Raf düzeni kontrol edilsin"
              className="min-h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
            />
          </label>

          <label className="block">
            <span className="mb-1.5 block text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
              Açıklama
            </span>
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Personelin görevi nasıl yapacağını açıkla..."
              className="min-h-24 w-full resize-none rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-3 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
            />
          </label>

          <div className="grid grid-cols-2 gap-2">
            <label className="block">
              <span className="mb-1.5 block text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                {taskMode === "routine" ? "Her gün saat" : "Bugün saat"}
              </span>
              <input
                type="time"
                value={dueTime}
                onChange={(event) => setDueTime(event.target.value)}
                className="min-h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
              />
            </label>

            <label className="block">
              <span className="mb-1.5 block text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                Öncelik
              </span>
              <select
                value={priority}
                onChange={(event) => setPriority(event.target.value as TaskAssignPriority)}
                className="min-h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
              >
                <option value="low">Düşük</option>
                <option value="normal">Normal</option>
                <option value="high">Yüksek</option>
                <option value="urgent">Acil</option>
              </select>
            </label>
          </div>

          <section>
            <p className="mb-2 text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
              Görev şartları
            </p>

            <div className="grid grid-cols-3 gap-2">
              <RequirementToggle
                label="Fotoğraf"
                icon={<Camera size={18} />}
                isActive={requiresPhoto}
                onToggle={() => setRequiresPhoto((value) => !value)}
              />

              <RequirementToggle
                label="Konum"
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
                label="Onay"
                icon={<FileCheck2 size={18} />}
                isActive={requiresManagerApproval}
                onToggle={() => setRequiresManagerApproval((value) => !value)}
              />
            </div>
          </section>

          <section className="rounded-[1.4rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                  Kaydetmeden önce
                </p>

                <h4 className="mt-1 text-sm font-black text-[var(--missio-text-main)]">
                  Görev özeti
                </h4>
              </div>

              <span className="rounded-full bg-cyan-100 px-2.5 py-1 text-[0.65rem] font-black text-cyan-800 dark:bg-cyan-950 dark:text-cyan-200">
                {selectedTaskModeLabel}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs font-bold">
              <div className="rounded-2xl bg-white/60 px-3 py-2 dark:bg-white/5">
                <p className="text-[0.62rem] font-black uppercase tracking-wide text-[var(--missio-text-muted)]">
                  Personel
                </p>
                <p className="mt-1 truncate text-[var(--missio-text-main)]">
                  {selectedUserLabel}
                </p>
              </div>

              <div className="rounded-2xl bg-white/60 px-3 py-2 dark:bg-white/5">
                <p className="text-[0.62rem] font-black uppercase tracking-wide text-[var(--missio-text-muted)]">
                  Saat
                </p>
                <p className="mt-1 truncate text-[var(--missio-text-main)]">
                  {selectedDueTimeLabel}
                </p>
              </div>

              <div className="col-span-2 rounded-2xl bg-white/60 px-3 py-2 dark:bg-white/5">
                <p className="text-[0.62rem] font-black uppercase tracking-wide text-[var(--missio-text-muted)]">
                  Şartlar
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
            {taskMode === "extra" ? "Ekstra görevi ata" : "Rutin görevi oluştur"}
          </button>
        </div>
      </div>
    </div>
  )
}
