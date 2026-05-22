import { useEffect, useMemo, useState } from "react"
import {
  Camera,
  FileCheck2,
  Loader2,
  MapPin,
  Plus,
  Send,
  Sparkles,
  X,
} from "lucide-react"

import {
  listBusinessUsers,
  type BusinessUser,
} from "../../services/businessUserService"
import {
  createExtraTask,
  createRoutineTaskTemplate,
  generateDailyRoutineTasks,
} from "../../services/taskService"

type BossTaskAssignCardProps = {
  businessId: number | null
  onChanged: () => void
}

type TaskAssignType = "extra" | "routine"
type TaskPriority = "low" | "normal" | "high" | "urgent"

const priorityOptions: { value: TaskPriority; label: string }[] = [
  {
    value: "low",
    label: "Düşük",
  },
  {
    value: "normal",
    label: "Normal",
  },
  {
    value: "high",
    label: "Yüksek",
  },
]

function getLocalTodayDateKey() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, "0")
  const day = String(now.getDate()).padStart(2, "0")

  return `${year}-${month}-${day}`
}

function buildDueAtUtc(timeValue: string) {
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

  const dueDate = new Date()
  dueDate.setHours(hour, minute, 0, 0)

  return dueDate.toISOString()
}

function getAssignableUsers(users: BusinessUser[]) {
  return users.filter((user) => {
    if (!user.is_active) {
      return false
    }

    return user.role === "staff" || user.role === "manager"
  })
}

function getSelectedUserLabel(users: BusinessUser[], selectedUserId: string) {
  const selectedUser = users.find((user) => String(user.id) === selectedUserId)

  if (!selectedUser) {
    return "Personel seçilmedi"
  }

  return `${selectedUser.full_name} @${selectedUser.username}`
}

function RequirementButton({
  icon,
  label,
  isActive,
  isDisabled = false,
  onClick,
}: {
  icon: React.ReactNode
  label: string
  isActive: boolean
  isDisabled?: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={isDisabled}
      className={
        isActive
          ? "flex min-h-16 flex-col items-center justify-center gap-1 rounded-2xl bg-cyan-500 px-3 text-sm font-black text-white shadow-lg shadow-cyan-500/20 transition active:scale-95 disabled:opacity-50"
          : "flex min-h-16 flex-col items-center justify-center gap-1 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-3 text-sm font-black text-[var(--missio-text-muted)] transition active:scale-95 disabled:cursor-not-allowed disabled:opacity-45"
      }
    >
      {icon}
      {label}
    </button>
  )
}

export function BossTaskAssignCard({
  businessId,
  onChanged,
}: BossTaskAssignCardProps) {
  const [users, setUsers] = useState<BusinessUser[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [isLoadingUsers, setIsLoadingUsers] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const [taskType, setTaskType] = useState<TaskAssignType>("extra")
  const [assignedToUserId, setAssignedToUserId] = useState("")
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [dueTimeLocal, setDueTimeLocal] = useState("")
  const [priority, setPriority] = useState<TaskPriority>("normal")
  const [requiresPhoto, setRequiresPhoto] = useState(false)
  const [requiresManagerApproval, setRequiresManagerApproval] = useState(false)

  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const assignableUsers = useMemo(() => getAssignableUsers(users), [users])
  const selectedUserLabel = getSelectedUserLabel(assignableUsers, assignedToUserId)
  const selectedTaskTypeLabel = taskType === "extra" ? "Ekstra görev" : "Rutin görev"
  const selectedTimeLabel = dueTimeLocal || "Saat belirtilmedi"

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
    void loadUsers()
  }, [businessId])

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

  function resetForm() {
    setTaskType("extra")
    setAssignedToUserId("")
    setTitle("")
    setDescription("")
    setDueTimeLocal("")
    setPriority("normal")
    setRequiresPhoto(false)
    setRequiresManagerApproval(false)
    setErrorMessage(null)
    setSuccessMessage(null)
  }

  function closePanel() {
    setIsOpen(false)
    resetForm()
  }

  async function handleCreateTask() {
    const selectedUserId = Number(assignedToUserId)

    if (!businessId) {
      setErrorMessage("Bu kullanıcı için işletme bilgisi bulunamadı.")
      return
    }

    if (!selectedUserId) {
      setErrorMessage("Görev atanacak personeli seçmelisin.")
      return
    }

    if (!title.trim()) {
      setErrorMessage("Görev başlığı zorunludur.")
      return
    }

    setIsSaving(true)
    setErrorMessage(null)
    setSuccessMessage(null)

    try {
      if (taskType === "extra") {
        await createExtraTask({
          assigned_to_user_id: selectedUserId,
          title: title.trim(),
          description: description.trim() || null,
          category_id: null,
          priority,
          due_at_utc: buildDueAtUtc(dueTimeLocal),
          requires_photo: requiresPhoto,
          requires_location: false,
          requires_manager_approval: requiresManagerApproval,
        })
      } else {
        await createRoutineTaskTemplate({
          assigned_to_user_id: selectedUserId,
          title: title.trim(),
          description: description.trim() || null,
          category_id: null,
          recurrence_type: "daily",
          default_priority: priority,
          default_due_time_local: dueTimeLocal || null,
          default_due_offset_minutes: null,
          requires_photo: requiresPhoto,
          requires_location: false,
          requires_manager_approval: requiresManagerApproval,
        })

        await generateDailyRoutineTasks({
          task_date: getLocalTodayDateKey(),
          assigned_to_user_id: selectedUserId,
        })
      }

      setSuccessMessage(
        taskType === "extra"
          ? "Ekstra görev başarıyla atandı."
          : "Rutin görev oluşturuldu ve bugüne işlendi.",
      )
      resetForm()
      onChanged()
      await loadUsers()
      setIsOpen(false)
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Görev atanamadı.")
      }
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <section className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
            Operasyon
          </p>

          <h2 className="mt-1 text-base font-black text-[var(--missio-text-main)]">
            Görev ata
          </h2>

          <p className="mt-1 text-xs font-bold leading-5 text-[var(--missio-text-muted)]">
            Yönetici ekranıyla aynı standart görev atama akışı.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary)] text-white shadow-lg shadow-teal-500/20 transition active:scale-95"
          aria-label="Görev ata"
        >
          <Plus size={22} />
        </button>
      </div>

      {successMessage && (
        <div className="mt-3 rounded-2xl bg-emerald-50 p-3 text-sm font-black text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-200">
          {successMessage}
        </div>
      )}

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-end justify-center overflow-hidden overscroll-none bg-slate-950/55 px-3 pb-[max(1rem,env(safe-area-inset-bottom))] pt-[max(7.5rem,env(safe-area-inset-top))] backdrop-blur-sm">
          <div className="max-h-[calc(100dvh-9rem)] w-full max-w-[430px] overflow-y-auto overscroll-contain rounded-[2rem] bg-[var(--missio-page-bg)] shadow-2xl">
            <div className="sticky top-0 z-10 border-b border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--missio-text-muted)]">
                    Yeni görev
                  </p>

                  <h3 className="mt-1 text-xl font-black text-[var(--missio-text-main)]">
                    {taskType === "extra" ? "Ekstra görev ata" : "Rutin görev oluştur"}
                  </h3>
                </div>

                <button
                  type="button"
                  onClick={closePanel}
                  className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[var(--missio-card-bg)] text-[var(--missio-text-main)] shadow-sm"
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
                    onClick={() => setTaskType("extra")}
                    className={
                      taskType === "extra"
                        ? "min-h-12 rounded-2xl bg-cyan-500 px-3 text-sm font-black text-white shadow-lg shadow-cyan-500/20"
                        : "min-h-12 rounded-2xl px-3 text-sm font-black text-[var(--missio-text-muted)]"
                    }
                  >
                    Ekstra
                  </button>

                  <button
                    type="button"
                    onClick={() => setTaskType("routine")}
                    className={
                      taskType === "routine"
                        ? "min-h-12 rounded-2xl bg-cyan-500 px-3 text-sm font-black text-white shadow-lg shadow-cyan-500/20"
                        : "min-h-12 rounded-2xl px-3 text-sm font-black text-[var(--missio-text-muted)]"
                    }
                  >
                    Rutin
                  </button>
                </div>

                <p className="mt-2 text-xs font-bold leading-5 text-[var(--missio-text-muted)]">
                  {taskType === "extra"
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
                    {assignableUsers.length} aktif
                  </span>
                </div>

                <select
                  value={assignedToUserId}
                  onChange={(event) => setAssignedToUserId(event.target.value)}
                  disabled={isLoadingUsers}
                  className="min-h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
                >
                  <option value="">
                    {isLoadingUsers ? "Personel yükleniyor..." : "Personel seç"}
                  </option>

                  {assignableUsers.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.full_name} (@{user.username})
                    </option>
                  ))}
                </select>
              </section>

              <section className="space-y-3">
                <label className="block">
                  <span className="mb-1 block text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                    Görev başlığı
                  </span>

                  <input
                    value={title}
                    onChange={(event) => setTitle(event.target.value)}
                    placeholder="Örn: Raf düzeni kontrol edilsin"
                    maxLength={200}
                    className="min-h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-3 text-sm font-bold text-[var(--missio-text-main)] outline-none placeholder:text-[var(--missio-text-muted)] focus:border-cyan-400"
                  />
                </label>

                <label className="block">
                  <span className="mb-1 block text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                    Açıklama
                  </span>

                  <textarea
                    value={description}
                    onChange={(event) => setDescription(event.target.value)}
                    placeholder="Personelin görevi nasıl yapacağını açıkla..."
                    maxLength={5000}
                    className="min-h-24 w-full resize-none rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-3 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none placeholder:text-[var(--missio-text-muted)] focus:border-cyan-400"
                  />
                </label>
              </section>

              <section className="grid grid-cols-2 gap-2">
                <label className="block">
                  <span className="mb-1 block text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                    Bugün saat
                  </span>

                  <input
                    type="time"
                    value={dueTimeLocal}
                    onChange={(event) => setDueTimeLocal(event.target.value)}
                    className="min-h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
                  />
                </label>

                <label className="block">
                  <span className="mb-1 block text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                    Öncelik
                  </span>

                  <select
                    value={priority}
                    onChange={(event) => setPriority(event.target.value as TaskPriority)}
                    className="min-h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
                  >
                    {priorityOptions.map((item) => (
                      <option key={item.value} value={item.value}>
                        {item.label}
                      </option>
                    ))}
                  </select>
                </label>
              </section>

              <section>
                <p className="mb-2 text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                  Görev şartları
                </p>

                <div className="grid grid-cols-3 gap-2">
                  <RequirementButton
                    icon={<Camera size={18} />}
                    label="Fotoğraf"
                    isActive={requiresPhoto}
                    onClick={() => setRequiresPhoto((value) => !value)}
                  />

                  <RequirementButton
                    icon={<MapPin size={18} />}
                    label="Konum"
                    isActive={false}
                    isDisabled
                    onClick={() => undefined}
                  />

                  <RequirementButton
                    icon={<FileCheck2 size={18} />}
                    label="Onay"
                    isActive={requiresManagerApproval}
                    onClick={() => setRequiresManagerApproval((value) => !value)}
                  />
                </div>
              </section>

              <section className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3">
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
                    {selectedTaskTypeLabel}
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
                      {selectedTimeLabel}
                    </p>
                  </div>

                  <div className="col-span-2 rounded-2xl bg-white/60 px-3 py-2 dark:bg-white/5">
                    <p className="text-[0.62rem] font-black uppercase tracking-wide text-[var(--missio-text-muted)]">
                      Şartlar
                    </p>
                    <p className="mt-1 text-[var(--missio-text-main)]">
                      {[
                        requiresPhoto ? "Fotoğraf" : null,
                        requiresManagerApproval ? "Yönetici onayı" : null,
                      ]
                        .filter(Boolean)
                        .join(" + ") || "Ek şart yok"}
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
                ) : taskType === "extra" ? (
                  <Send size={18} />
                ) : (
                  <Sparkles size={18} />
                )}
                {taskType === "extra" ? "Ekstra görevi ata" : "Rutin görevi oluştur"}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
