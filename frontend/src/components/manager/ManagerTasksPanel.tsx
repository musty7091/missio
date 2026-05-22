import {
  AlertCircle,
  CalendarClock,
  CheckCircle2,
  ClipboardCheck,
  ClipboardList,
  FileCheck2,
  ImageIcon,
  Loader2,
  MapPin,
  Plus,
  RefreshCw,
  Send,
  UserRound,
  UsersRound,
  X,
} from "lucide-react"
import { type ReactNode, useEffect, useMemo, useState } from "react"
import {
  listBusinessUsers,
  type BusinessUser,
} from "../../services/businessUserService"
import {
  createExtraTask,
  createRoutineTaskTemplate,
  generateDailyRoutineTasks,
  listBusinessTasks,
} from "../../services/taskService"
import { TaskCard } from "../tasks/TaskCard"
import type { TodayTask } from "../../types/task"
import { mapApiTaskToTodayTask } from "../../utils/apiTaskMapper"
import { getPriorityLabel, getStatusLabel } from "../../utils/taskLabels"

type ManagerTasksPanelProps = {
  businessId: number | null
  currentUserId: number
  busyTaskId: number | null
  onOpenOwnTaskDetails: (task: TodayTask) => void
  onChanged: () => void
}

type PriorityValue = "low" | "normal" | "high" | "urgent"

type TaskKind = "extra" | "routine"

type StaffMetrics = {
  total: number
  open: number
  done: number
  approvalPending: number
  rejected: number
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

  if (Number.isNaN(hour) || Number.isNaN(minute)) {
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

function formatTaskTime(value: string | null) {
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

function getStaffName(task: TodayTask) {
  if (task.assignedToUserFullName) {
    return task.assignedToUserFullName
  }

  if (task.assignedToUsername) {
    return task.assignedToUsername
  }

  if (task.assignedToUserId) {
    return `Personel ID #${task.assignedToUserId}`
  }

  return "Personel yok"
}

function getReadableStatusLabel(task: TodayTask) {
  if (task.status === "completed" && !task.requiresManagerApproval) {
    return "Tamamlandı"
  }

  return getStatusLabel(task.status)
}

function getStaffMetrics(tasks: TodayTask[], staffId: number): StaffMetrics {
  const staffTasks = tasks.filter((task) => task.assignedToUserId === staffId)

  return {
    total: staffTasks.length,
    open: staffTasks.filter(
      (task) =>
        task.status === "assigned" ||
        task.status === "in_progress" ||
        task.status === "rejected",
    ).length,
    done: staffTasks.filter(
      (task) =>
        task.status === "approved" ||
        (task.status === "completed" && !task.requiresManagerApproval),
    ).length,
    approvalPending: staffTasks.filter(
      (task) => task.status === "completed" && task.requiresManagerApproval,
    ).length,
    rejected: staffTasks.filter((task) => task.status === "rejected").length,
  }
}

function getTaskStatusClass(task: TodayTask) {
  if (task.status === "rejected") {
    return "rounded-full bg-red-100 px-2 py-0.5 text-[0.6rem] font-black text-red-700 dark:bg-red-950 dark:text-red-200"
  }

  if (task.status === "approved") {
    return "rounded-full bg-emerald-100 px-2 py-0.5 text-[0.6rem] font-black text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200"
  }

  if (task.status === "completed") {
    return "rounded-full bg-cyan-100 px-2 py-0.5 text-[0.6rem] font-black text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200"
  }

  if (task.status === "in_progress") {
    return "rounded-full bg-amber-100 px-2 py-0.5 text-[0.6rem] font-black text-amber-700 dark:bg-amber-950 dark:text-amber-200"
  }

  return "rounded-full bg-slate-100 px-2 py-0.5 text-[0.6rem] font-black text-slate-700 dark:bg-slate-800 dark:text-slate-200"
}

function StatTile({
  label,
  value,
  tone = "default",
}: {
  label: string
  value: number
  tone?: "default" | "warning" | "success"
}) {
  const className =
    tone === "success"
      ? "rounded-2xl bg-emerald-500/15 px-3 py-2 ring-1 ring-emerald-400/20"
      : tone === "warning"
        ? "rounded-2xl bg-amber-500/15 px-3 py-2 ring-1 ring-amber-400/20"
        : "rounded-2xl bg-white/10 px-3 py-2"

  return (
    <div className={className}>
      <p className="text-xl font-black leading-none text-white">{value}</p>
      <p className="mt-1 text-[0.64rem] font-bold text-slate-300">{label}</p>
    </div>
  )
}

function StaffCard({
  user,
  metrics,
  staffTasks,
  busyTaskId,
  onOpenTaskDetails,
}: {
  user: BusinessUser
  metrics: StaffMetrics
  staffTasks: TodayTask[]
  busyTaskId: number | null
  onOpenTaskDetails: (task: TodayTask) => void
}) {
  const [isExpanded, setIsExpanded] = useState(false)
  const hasTasks = staffTasks.length > 0

  return (
    <article className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
      <button
        type="button"
        onClick={() => {
          if (hasTasks) {
            setIsExpanded((value) => !value)
          }
        }}
        className="w-full text-left"
      >
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-sm font-black text-cyan-800 dark:text-cyan-200">
            {getInitials(user.full_name)}
          </div>

          <div className="min-w-0 flex-1">
            <h3 className="truncate text-sm font-black text-[var(--missio-text-main)]">
              {user.full_name}
            </h3>
            <p className="mt-0.5 truncate text-xs font-bold text-[var(--missio-text-muted)]">
              @{user.username}
            </p>
          </div>

          <div className="rounded-2xl bg-[var(--missio-page-bg)] px-3 py-2 text-center">
            <p className="text-base font-black leading-none text-[var(--missio-text-main)]">
              {metrics.total}
            </p>
            <p className="mt-1 text-[0.58rem] font-black text-[var(--missio-text-muted)]">
              görev
            </p>
          </div>
        </div>

        <div className="mt-3 grid grid-cols-3 gap-2">
          <div className="rounded-2xl bg-[var(--missio-page-bg)] px-2 py-2 text-center">
            <p className="text-sm font-black text-[var(--missio-text-main)]">
              {metrics.open}
            </p>
            <p className="text-[0.58rem] font-black text-[var(--missio-text-muted)]">
              Açık
            </p>
          </div>

          <div className="rounded-2xl bg-[var(--missio-page-bg)] px-2 py-2 text-center">
            <p className="text-sm font-black text-[var(--missio-text-main)]">
              {metrics.approvalPending}
            </p>
            <p className="text-[0.58rem] font-black text-[var(--missio-text-muted)]">
              Onay
            </p>
          </div>

          <div className="rounded-2xl bg-[var(--missio-page-bg)] px-2 py-2 text-center">
            <p
              className={
                metrics.rejected > 0
                  ? "text-sm font-black text-red-600 dark:text-red-300"
                  : "text-sm font-black text-[var(--missio-text-main)]"
              }
            >
              {metrics.rejected}
            </p>
            <p className="text-[0.58rem] font-black text-[var(--missio-text-muted)]">
              Red
            </p>
          </div>
        </div>

        <div className="mt-3 rounded-2xl bg-[var(--missio-page-bg)] px-3 py-2 text-center text-xs font-black text-[var(--missio-text-muted)]">
          {hasTasks
            ? isExpanded
              ? "Görevleri gizle"
              : "Görevleri göster"
            : "Bugün görev yok"}
        </div>
      </button>

      {isExpanded && hasTasks && (
        <div className="mt-3 space-y-2 border-t border-[var(--missio-border)] pt-3">
          {staffTasks.map((task) => (
            <button
              key={task.id}
              type="button"
              onClick={() => onOpenTaskDetails(task)}
              disabled={busyTaskId === task.id}
              className="w-full rounded-[1.2rem] border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-3 text-left transition active:scale-[0.99] disabled:cursor-wait disabled:opacity-60"
            >
              <div className="mb-1.5 flex flex-wrap items-center gap-1.5">
                <span className={getTaskStatusClass(task)}>
                  {getReadableStatusLabel(task)}
                </span>

                <span className="rounded-full bg-violet-50 px-2 py-0.5 text-[0.6rem] font-black text-violet-700 dark:bg-violet-950 dark:text-violet-200">
                  {task.taskType === "routine" ? "Rutin" : "Ekstra"}
                </span>

                <span className="rounded-full bg-[var(--missio-card-bg)] px-2 py-0.5 text-[0.6rem] font-black text-[var(--missio-text-muted)]">
                  {getPriorityLabel(task.priority)}
                </span>
              </div>

              <h4 className="truncate text-sm font-black text-[var(--missio-text-main)]">
                {task.title}
              </h4>

              <div className="mt-1.5 flex flex-wrap items-center gap-2 text-[0.68rem] font-bold text-[var(--missio-text-muted)]">
                <span className="inline-flex items-center gap-1">
                  <CalendarClock size={12} />
                  {formatTaskTime(task.dueAtUtc)}
                </span>

                {task.requiresPhoto && (
                  <span className="inline-flex items-center gap-1">
                    <ImageIcon size={12} />
                    Foto
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
            </button>
          ))}
        </div>
      )}
    </article>
  )
}

function ManagerTaskRow({ task }: { task: TodayTask }) {
  const staffName = getStaffName(task)

  return (
    <article className="rounded-[1.35rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
      <div className="flex items-start gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-sm font-black text-cyan-800 dark:text-cyan-200">
          {getInitials(staffName)}
        </div>

        <div className="min-w-0 flex-1">
          <div className="mb-1.5 flex flex-wrap gap-1.5">
            <span className={getTaskStatusClass(task)}>
              {getReadableStatusLabel(task)}
            </span>

            <span className="rounded-full bg-violet-50 px-2 py-0.5 text-[0.6rem] font-black text-violet-700 dark:bg-violet-950 dark:text-violet-200">
              {task.taskType === "routine" ? "Rutin" : "Ekstra"}
            </span>

            <span className="rounded-full bg-[var(--missio-page-bg)] px-2 py-0.5 text-[0.6rem] font-black text-[var(--missio-text-muted)]">
              {getPriorityLabel(task.priority)}
            </span>
          </div>

          <h3 className="truncate text-sm font-black text-[var(--missio-text-main)]">
            {task.title}
          </h3>

          <div className="mt-1.5 flex flex-wrap items-center gap-2 text-[0.7rem] font-bold text-[var(--missio-text-muted)]">
            <span className="inline-flex items-center gap-1">
              <UserRound size={12} />
              {staffName}
            </span>

            <span className="inline-flex items-center gap-1">
              <CalendarClock size={12} />
              {formatTaskTime(task.dueAtUtc)}
            </span>

            {task.requiresPhoto && (
              <span className="inline-flex items-center gap-1">
                <ImageIcon size={12} />
                Foto
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
      </div>
    </article>
  )
}

function RequirementToggle({
  label,
  icon,
  isActive,
  onToggle,
}: {
  label: string
  icon: ReactNode
  isActive: boolean
  onToggle: () => void
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={
        isActive
          ? "flex min-h-14 flex-col items-center justify-center gap-1 rounded-2xl bg-cyan-500 px-2 py-3 text-xs font-black text-white shadow-lg shadow-cyan-500/20"
          : "flex min-h-14 flex-col items-center justify-center gap-1 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-2 py-3 text-xs font-black text-[var(--missio-text-muted)]"
      }
    >
      {icon}
      {label}
    </button>
  )
}

function TaskComposerSheet({
  staffUsers,
  taskKind,
  selectedUserId,
  title,
  description,
  dueTime,
  priority,
  requiresPhoto,
  requiresLocation,
  requiresManagerApproval,
  isSaving,
  onClose,
  onTaskKindChange,
  onSelectedUserIdChange,
  onTitleChange,
  onDescriptionChange,
  onDueTimeChange,
  onPriorityChange,
  onRequiresPhotoChange,
  onRequiresLocationChange,
  onRequiresManagerApprovalChange,
  onCreate,
}: {
  staffUsers: BusinessUser[]
  taskKind: TaskKind
  selectedUserId: string
  title: string
  description: string
  dueTime: string
  priority: PriorityValue
  requiresPhoto: boolean
  requiresLocation: boolean
  requiresManagerApproval: boolean
  isSaving: boolean
  onClose: () => void
  onTaskKindChange: (value: TaskKind) => void
  onSelectedUserIdChange: (value: string) => void
  onTitleChange: (value: string) => void
  onDescriptionChange: (value: string) => void
  onDueTimeChange: (value: string) => void
  onPriorityChange: (value: PriorityValue) => void
  onRequiresPhotoChange: () => void
  onRequiresLocationChange: () => void
  onRequiresManagerApprovalChange: () => void
  onCreate: () => void
}) {
  const selectedStaffForPreview = staffUsers.find(
    (user) => String(user.id) === selectedUserId,
  )
  const selectedStaffName = selectedStaffForPreview
    ? selectedStaffForPreview.full_name
    : "Personel seçilmedi"
  const selectedTaskKindLabel =
    taskKind === "routine" ? "Rutin görev" : "Ekstra görev"
  const selectedDueTimeLabel = dueTime ? dueTime : "Saat belirtilmedi"
  const requirementSummary =
    [
      requiresPhoto ? "Fotoğraf" : null,
      requiresLocation ? "Konum" : null,
      requiresManagerApproval ? "Yönetici onayı" : null,
    ]
      .filter(Boolean)
      .join(" + ") || "Ek şart yok"

  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center bg-slate-950/45 px-3 pb-3 backdrop-blur-sm">
      <div className="max-h-[92vh] w-full max-w-md overflow-hidden rounded-[2rem] bg-[var(--missio-card-bg)] shadow-2xl">
        <div className="flex items-center justify-between border-b border-[var(--missio-border)] px-4 py-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--missio-text-muted)]">
              Yeni görev
            </p>
            <h3 className="text-lg font-black text-[var(--missio-text-main)]">
              {taskKind === "routine" ? "Rutin görev oluştur" : "Ekstra görev ata"}
            </h3>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="flex h-10 w-10 items-center justify-center rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] text-[var(--missio-text-muted)]"
            aria-label="Kapat"
          >
            <X size={19} />
          </button>
        </div>

        <div className="max-h-[calc(92vh-76px)] space-y-3 overflow-y-auto px-4 py-4">
          <div>
            <span className="mb-2 block text-xs font-black text-[var(--missio-text-muted)]">
              Görev tipi
            </span>

            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={(event) => {
                  event.preventDefault()
                  onTaskKindChange("extra")
                }}
                className={
                  taskKind === "extra"
                    ? "rounded-2xl bg-cyan-500 px-3 py-3 text-sm font-black text-white shadow-lg shadow-cyan-500/20"
                    : "rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-3 py-3 text-sm font-black text-[var(--missio-text-muted)]"
                }
              >
                Ekstra
              </button>

              <button
                type="button"
                onClick={(event) => {
                  event.preventDefault()
                  onTaskKindChange("routine")
                }}
                className={
                  taskKind === "routine"
                    ? "rounded-2xl bg-cyan-500 px-3 py-3 text-sm font-black text-white shadow-lg shadow-cyan-500/20"
                    : "rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-3 py-3 text-sm font-black text-[var(--missio-text-muted)]"
                }
              >
                Rutin
              </button>
            </div>

            <p className="mt-2 text-[0.7rem] font-bold leading-5 text-[var(--missio-text-muted)]">
              {taskKind === "routine"
                ? "Rutin görev bu işletmeye özel günlük tekrar şablonu olarak kaydedilir ve bugünün görevlerine de işlenir."
                : "Ekstra görev bugüne özel tek seferlik iş olarak atanır."}
            </p>

            <div className="mt-2 rounded-2xl bg-[var(--missio-page-bg)] px-3 py-2 text-xs font-black text-[var(--missio-text-main)]">
              Seçili görev tipi: {taskKind === "routine" ? "Rutin görev" : "Ekstra görev"}
            </div>
          </div>

          <label className="block">
            <div className="mb-1.5 flex items-center justify-between gap-3">
              <span className="block text-xs font-black text-[var(--missio-text-muted)]">
                Personel
              </span>

              <span className="rounded-full bg-[var(--missio-primary-soft)] px-2.5 py-1 text-[0.65rem] font-black text-cyan-700 dark:text-cyan-200">
                {staffUsers.length} aktif
              </span>
            </div>

            <select
              value={selectedUserId}
              onChange={(event) => onSelectedUserIdChange(event.target.value)}
              className="h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
            >
              {staffUsers.length === 0 ? (
                <option value="">Aktif personel yok</option>
              ) : (
                staffUsers.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.full_name} (@{user.username})
                  </option>
                ))
              )}
            </select>
          </label>

          <label className="block">
            <span className="mb-1.5 block text-xs font-black text-[var(--missio-text-muted)]">
              Görev başlığı
            </span>
            <input
              value={title}
              onChange={(event) => onTitleChange(event.target.value)}
              placeholder="Örn: Raf düzeni kontrol edilsin"
              className="h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
            />
          </label>

          <label className="block">
            <span className="mb-1.5 block text-xs font-black text-[var(--missio-text-muted)]">
              Açıklama
            </span>
            <textarea
              value={description}
              onChange={(event) => onDescriptionChange(event.target.value)}
              placeholder="Personelin görevi nasıl yapacağını açıkla..."
              className="min-h-24 w-full resize-none rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-3 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
            />
          </label>

          <div className="grid grid-cols-2 gap-2">
            <label className="block">
              <span className="mb-1.5 block text-xs font-black text-[var(--missio-text-muted)]">
                {taskKind === "routine" ? "Her gün saat" : "Bugün saat"}
              </span>
              <input
                type="time"
                value={dueTime}
                onChange={(event) => onDueTimeChange(event.target.value)}
                className="h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
              />
            </label>

            <label className="block">
              <span className="mb-1.5 block text-xs font-black text-[var(--missio-text-muted)]">
                Öncelik
              </span>
              <select
                value={priority}
                onChange={(event) => onPriorityChange(event.target.value as PriorityValue)}
                className="h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-3 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-cyan-400"
              >
                <option value="low">Düşük</option>
                <option value="normal">Normal</option>
                <option value="high">Yüksek</option>
                <option value="urgent">Acil</option>
              </select>
            </label>
          </div>

          <div>
            <p className="mb-2 text-xs font-black text-[var(--missio-text-muted)]">
              Görev şartları
            </p>

            <div className="grid grid-cols-3 gap-2">
              <RequirementToggle
                label="Fotoğraf"
                icon={<ImageIcon size={18} />}
                isActive={requiresPhoto}
                onToggle={onRequiresPhotoChange}
              />

              <RequirementToggle
                label="Konum"
                icon={<MapPin size={18} />}
                isActive={requiresLocation}
                onToggle={onRequiresLocationChange}
              />

              <RequirementToggle
                label="Onay"
                icon={<FileCheck2 size={18} />}
                isActive={requiresManagerApproval}
                onToggle={onRequiresManagerApprovalChange}
              />
            </div>
          </div>

          <div className="rounded-[1.4rem] border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-3">
            <div className="mb-2 flex items-center justify-between gap-3">
              <p className="text-xs font-black text-[var(--missio-text-muted)]">
                Kaydetmeden önce
              </p>

              <span className="rounded-full bg-[var(--missio-primary-soft)] px-2.5 py-1 text-[0.65rem] font-black text-cyan-700 dark:text-cyan-200">
                {selectedTaskKindLabel}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[0.72rem] font-bold text-[var(--missio-text-muted)]">
              <div className="rounded-2xl bg-[var(--missio-card-bg)] px-3 py-2">
                <p className="text-[0.6rem] font-black uppercase tracking-wide opacity-70">
                  Personel
                </p>
                <p className="mt-1 truncate text-[var(--missio-text-main)]">
                  {selectedStaffName}
                </p>
              </div>

              <div className="rounded-2xl bg-[var(--missio-card-bg)] px-3 py-2">
                <p className="text-[0.6rem] font-black uppercase tracking-wide opacity-70">
                  Saat
                </p>
                <p className="mt-1 truncate text-[var(--missio-text-main)]">
                  {selectedDueTimeLabel}
                </p>
              </div>

              <div className="col-span-2 rounded-2xl bg-[var(--missio-card-bg)] px-3 py-2">
                <p className="text-[0.6rem] font-black uppercase tracking-wide opacity-70">
                  Şartlar
                </p>
                <p className="mt-1 truncate text-[var(--missio-text-main)]">
                  {requirementSummary}
                </p>
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={onCreate}
            disabled={isSaving || staffUsers.length === 0}
            className="flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 py-3 text-sm font-black text-white shadow-lg shadow-teal-500/20 transition active:scale-95 disabled:cursor-wait disabled:opacity-60"
          >
            {isSaving ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
            {taskKind === "routine" ? "Rutin görevi kaydet" : "Ekstra görevi ata"}
          </button>
        </div>
      </div>
    </div>
  )
}

export function ManagerTasksPanel({
  businessId,
  currentUserId,
  busyTaskId,
  onOpenOwnTaskDetails,
  onChanged,
}: ManagerTasksPanelProps) {
  const [users, setUsers] = useState<BusinessUser[]>([])
  const [tasks, setTasks] = useState<TodayTask[]>([])
  const [isComposerOpen, setIsComposerOpen] = useState(false)
  const [selectedUserId, setSelectedUserId] = useState("")
  const [taskKind, setTaskKind] = useState<TaskKind>("extra")
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [dueTime, setDueTime] = useState("")
  const [priority, setPriority] = useState<PriorityValue>("normal")
  const [requiresPhoto, setRequiresPhoto] = useState(false)
  const [requiresLocation, setRequiresLocation] = useState(false)
  const [requiresManagerApproval, setRequiresManagerApproval] = useState(true)
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const staffUsers = useMemo(
    () => users.filter((user) => user.role === "staff" && user.is_active),
    [users],
  )

  const operationStats = useMemo(() => {
    return {
      total: tasks.length,
      open: tasks.filter(
        (task) =>
          task.status === "assigned" ||
          task.status === "in_progress" ||
          task.status === "rejected",
      ).length,
      approvalPending: tasks.filter(
        (task) => task.status === "completed" && task.requiresManagerApproval,
      ).length,
      done: tasks.filter(
        (task) =>
          task.status === "approved" ||
          (task.status === "completed" && !task.requiresManagerApproval),
      ).length,
    }
  }, [tasks])

  const myTasks = useMemo(
    () => tasks.filter((task) => task.assignedToUserId === currentUserId),
    [tasks, currentUserId],
  )

  const recentTasks = useMemo(
    () =>
      tasks
        .filter((task) => task.assignedToUserId !== currentUserId)
        .slice(0, 8),
    [tasks, currentUserId],
  )

  useEffect(() => {
    if (staffUsers.length === 0) {
      setSelectedUserId("")
      return
    }

    const selectedUserExists = staffUsers.some(
      (user) => String(user.id) === selectedUserId,
    )

    if (!selectedUserExists) {
      setSelectedUserId(String(staffUsers[0].id))
    }
  }, [staffUsers, selectedUserId])

  async function loadManagerData() {
    if (businessId === null) {
      setErrorMessage("Bu kullanıcı için işletme bilgisi bulunamadı.")
      return
    }

    setIsLoading(true)
    setErrorMessage(null)

    try {
      const [usersResponse, tasksResponse] = await Promise.all([
        listBusinessUsers(businessId),
        listBusinessTasks({
          businessId,
          taskDate: getLocalTodayDateKey(),
          limit: 500,
          offset: 0,
        }),
      ])

      setUsers(usersResponse)
      setTasks(tasksResponse.tasks.map(mapApiTaskToTodayTask))
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Manager görev verileri alınamadı.")
      }
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadManagerData()
  }, [businessId])

  function clearForm() {
    setTitle("")
    setDescription("")
    setDueTime("")
    setPriority("normal")
    setTaskKind("extra")
    setRequiresPhoto(false)
    setRequiresLocation(false)
    setRequiresManagerApproval(true)
  }

  async function handleCreateExtraTask() {
    if (businessId === null) {
      setErrorMessage("Bu kullanıcı için işletme bilgisi bulunamadı.")
      return
    }

    const assignedUserId = Number(selectedUserId)
    const trimmedTitle = title.trim()
    const trimmedDescription = description.trim()

    if (!assignedUserId) {
      setErrorMessage("Lütfen görev atanacak personeli seç.")
      return
    }

    if (trimmedTitle.length < 2) {
      setErrorMessage("Görev başlığı en az 2 karakter olmalıdır.")
      return
    }

    setIsSaving(true)
    setErrorMessage(null)
    setMessage(null)

    try {
      if (taskKind === "routine") {
        await createRoutineTaskTemplate({
          assigned_to_user_id: assignedUserId,
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
          assigned_to_user_id: assignedUserId,
        })

        setMessage("Rutin görev oluşturuldu ve bugünün görevlerine işlendi.")
      } else {
        await createExtraTask({
          assigned_to_user_id: assignedUserId,
          title: trimmedTitle,
          description: trimmedDescription || null,
          category_id: null,
          priority,
          due_at_utc: buildDueAtUtcFromLocalTime(dueTime),
          requires_photo: requiresPhoto,
          requires_location: requiresLocation,
          requires_manager_approval: requiresManagerApproval,
        })

        setMessage("Ekstra görev personele atandı.")
      }

      clearForm()
      setIsComposerOpen(false)

      await loadManagerData()
      onChanged()
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

  return (
    <section className="flex flex-1 flex-col pb-24">
      <div className="mb-4 rounded-[1.8rem] bg-slate-950 p-4 text-white shadow-xl shadow-slate-950/15">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-black text-cyan-200">
              <ClipboardCheck size={14} />
              Operasyon merkezi
            </div>

            <h2 className="mt-3 text-2xl font-black leading-tight">
              Bugünün görevleri
            </h2>

            <p className="mt-2 text-sm font-semibold leading-5 text-slate-300">
              Personel işleri, açık görevler ve onay bekleyen işler tek ekranda.
            </p>
          </div>

          <button
            type="button"
            onClick={() => void loadManagerData()}
            disabled={isLoading}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/10 text-cyan-200 transition active:scale-95 disabled:opacity-60"
            aria-label="Yenile"
            title="Yenile"
          >
            <RefreshCw size={19} />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <StatTile label="Toplam görev" value={operationStats.total} />
          <StatTile label="Açık iş" value={operationStats.open} tone="warning" />
          <StatTile label="Onay bekleyen" value={operationStats.approvalPending} />
          <StatTile label="Tamamlanan" value={operationStats.done} tone="success" />
        </div>
      </div>

      {errorMessage && (
        <div className="mb-3 flex gap-2 rounded-[1.4rem] border border-red-200 bg-red-50 p-3 text-sm font-black text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
          <AlertCircle size={18} />
          <span>{errorMessage}</span>
        </div>
      )}

      {message && (
        <div className="mb-3 flex gap-2 rounded-[1.4rem] border border-emerald-200 bg-emerald-50 p-3 text-sm font-black text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
          <CheckCircle2 size={18} />
          <span>{message}</span>
        </div>
      )}

      <div className="mb-4 rounded-[1.7rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-black text-[var(--missio-text-main)]">
              Görevlerim
            </h3>
            <p className="text-xs font-bold text-[var(--missio-text-muted)]">
              Manager olarak sana atanan işler
            </p>
          </div>

          <div className="rounded-full bg-[var(--missio-primary-soft)] px-3 py-1.5 text-xs font-black text-cyan-700 dark:text-cyan-200">
            {myTasks.length}
          </div>
        </div>

        {myTasks.length === 0 ? (
          <div className="rounded-[1.4rem] border border-dashed border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-4 text-center text-sm font-bold text-[var(--missio-text-muted)]">
            Bugün sana atanmış görev yok.
          </div>
        ) : (
          <div className="space-y-2.5">
            {myTasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                isBusy={busyTaskId === task.id}
                onOpenDetails={onOpenOwnTaskDetails}
              />
            ))}
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={() => setIsComposerOpen(true)}
        className="mb-4 flex min-h-14 w-full items-center justify-center gap-2 rounded-[1.5rem] bg-[var(--missio-primary)] px-4 py-3 text-sm font-black text-white shadow-lg shadow-teal-500/20 transition active:scale-95"
      >
        <Plus size={20} />
        Yeni görev ata
      </button>

      <div className="mb-4">
        <div className="mb-2 flex items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-black text-[var(--missio-text-main)]">
              Personel durumu
            </h3>
            <p className="text-xs font-bold text-[var(--missio-text-muted)]">
              Bugünkü görev dağılımı
            </p>
          </div>

          <div className="inline-flex items-center gap-1.5 rounded-full bg-[var(--missio-primary-soft)] px-3 py-1.5 text-xs font-black text-cyan-700 dark:text-cyan-200">
            <UsersRound size={14} />
            {staffUsers.length}
          </div>
        </div>

        {staffUsers.length === 0 ? (
          <div className="rounded-[1.6rem] border border-dashed border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-5 text-center text-sm font-bold text-[var(--missio-text-muted)]">
            Aktif personel bulunamadı.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-2.5">
            {staffUsers.map((user) => {
              const staffTasks = tasks.filter(
                (task) => task.assignedToUserId === user.id,
              )

              return (
                <StaffCard
                  key={user.id}
                  user={user}
                  metrics={getStaffMetrics(tasks, user.id)}
                  staffTasks={staffTasks}
                  busyTaskId={busyTaskId}
                  onOpenTaskDetails={onOpenOwnTaskDetails}
                />
              )
            })}
          </div>
        )}
      </div>

      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-black text-[var(--missio-text-main)]">
            Son görevler
          </h3>
          <p className="text-xs font-bold text-[var(--missio-text-muted)]">
            Bugün oluşturulan veya takip edilen işler
          </p>
        </div>

        <div className="rounded-full bg-[var(--missio-page-bg)] px-3 py-1.5 text-xs font-black text-[var(--missio-text-muted)]">
          {tasks.length}
        </div>
      </div>

      {isLoading ? (
        <div className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 text-sm font-black text-[var(--missio-text-muted)]">
          Manager görev ekranı yükleniyor...
        </div>
      ) : tasks.length === 0 ? (
        <div className="rounded-[1.7rem] border border-dashed border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-6 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-3xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
            <ClipboardList size={28} />
          </div>

          <h3 className="mt-4 text-lg font-black">Bugün atanmış görev yok</h3>

          <p className="mt-2 text-sm font-semibold leading-6 text-[var(--missio-text-muted)]">
            Yeni görev ata butonuyla temiz veriden ilk görevi oluşturabilirsin.
          </p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {recentTasks.map((task) => (
            <ManagerTaskRow key={task.id} task={task} />
          ))}
        </div>
      )}

      {isComposerOpen && (
        <TaskComposerSheet
          staffUsers={staffUsers}
          taskKind={taskKind}
          selectedUserId={selectedUserId}
          title={title}
          description={description}
          dueTime={dueTime}
          priority={priority}
          requiresPhoto={requiresPhoto}
          requiresLocation={requiresLocation}
          requiresManagerApproval={requiresManagerApproval}
          isSaving={isSaving}
          onClose={() => setIsComposerOpen(false)}
          onTaskKindChange={(value) => setTaskKind(value)}
          onSelectedUserIdChange={setSelectedUserId}
          onTitleChange={setTitle}
          onDescriptionChange={setDescription}
          onDueTimeChange={setDueTime}
          onPriorityChange={setPriority}
          onRequiresPhotoChange={() => setRequiresPhoto((value) => !value)}
          onRequiresLocationChange={() => setRequiresLocation((value) => !value)}
          onRequiresManagerApprovalChange={() =>
            setRequiresManagerApproval((value) => !value)
          }
          onCreate={() => void handleCreateExtraTask()}
        />
      )}
    </section>
  )
}

