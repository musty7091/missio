import { useEffect, useMemo, useState, type ReactNode } from "react"
import {
  BarChart3,
  ClipboardCheck,
  MapPin,
  PlusSquare,
  RefreshCw,
  UserPlus,
  UsersRound,
  X,
} from "lucide-react"
import { useTranslation } from "../../i18n/language"

import {
  listDailyOperationClosures,
  type DailyOperationClosure,
} from "../../services/dailyClosureService"
import { createBusinessUser, type BusinessUserRole } from "../../services/businessUserService"
import { listBusinessTasks } from "../../services/taskService"
import type { UserMeResponse } from "../../types/auth"
import type { TodayTask } from "../../types/task"
import { mapApiTaskToTodayTask } from "../../utils/apiTaskMapper"
import { LocationCheckRequestPanel } from "../location-checks/LocationCheckRequestPanel"
import { BilingualUserManagementPanel } from "../profile/BilingualUserManagementPanel"
import { TaskAssignSheet } from "../tasks/TaskAssignSheet"

type BossDashboardPanelProps = {
  businessId: number | null
  currentUser?: UserMeResponse
  onOpenApprovals: () => void
  onOpenReports: () => void
}

type CreateUserFormState = {
  full_name: string
  username: string
  password: string
  role: BusinessUserRole
  email: string
}

const emptyCreateUserForm: CreateUserFormState = {
  full_name: "",
  username: "",
  password: "",
  role: "staff",
  email: "",
}

function getLocalTodayDateKey() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, "0")
  const day = String(now.getDate()).padStart(2, "0")

  return `${year}-${month}-${day}`
}

function isTaskCompletedOrClosed(task: TodayTask) {
  if (task.status === "approved") {
    return true
  }

  if (task.status === "completed" && !task.requiresManagerApproval) {
    return true
  }

  return false
}

function isApprovalWaiting(task: TodayTask) {
  return task.status === "completed" && task.requiresManagerApproval
}

function getClosureStatusText(
  todayClosure: DailyOperationClosure | null,
  isTurkish: boolean,
) {
  if (!todayClosure) {
    return isTurkish ? "Bekleniyor" : "Waiting"
  }

  if (todayClosure.status === "closed_clean") {
    return isTurkish ? "Sorunsuz kapandı" : "Closed clean"
  }

  if (todayClosure.status === "closed_with_issues") {
    return isTurkish ? "Kontrol gerekli" : "Needs review"
  }

  return isTurkish ? "Rapor hazır" : "Report ready"
}

function getClosureStatusTone(todayClosure: DailyOperationClosure | null) {
  if (!todayClosure) {
    return "bg-slate-700/80 text-slate-100"
  }

  if (todayClosure.status === "closed_with_issues") {
    return "bg-amber-300 text-slate-950"
  }

  return "bg-emerald-300 text-slate-950"
}

function normalizeOptionalEmail(value: string) {
  const normalizedValue = value.trim().toLowerCase()
  return normalizedValue ? normalizedValue : null
}

function ActionSheet({
  isOpen,
  title,
  onClose,
  children,
}: {
  isOpen: boolean
  title: string
  onClose: () => void
  children: ReactNode
}) {
  if (!isOpen) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/55 px-3 pb-3 pt-16 backdrop-blur-sm">
      <div className="max-h-[88vh] w-full max-w-md overflow-hidden rounded-[2rem] bg-[var(--missio-page-bg)] shadow-2xl">
        <div className="flex items-center justify-between gap-3 border-b border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-3">
          <h2 className="text-base font-black text-[var(--missio-text-main)]">
            {title}
          </h2>

          <button
            type="button"
            onClick={onClose}
            className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[var(--missio-page-bg)] text-[var(--missio-text-main)] transition active:scale-95"
            aria-label="Kapat"
          >
            <X size={20} />
          </button>
        </div>

        <div className="max-h-[calc(88vh-4rem)] overflow-y-auto p-3">
          {children}
        </div>
      </div>
    </div>
  )
}

function QuickActionCard({
  title,
  icon,
  onClick,
  badge,
}: {
  title: string
  icon: ReactNode
  onClick: () => void
  badge?: string | number | null
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="relative flex min-h-[7.2rem] flex-col items-center justify-center rounded-[1.6rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 text-center shadow-sm transition active:scale-[0.98]"
    >
      {badge !== null && badge !== undefined && badge !== "" && (
        <span className="absolute right-3 top-3 min-w-6 rounded-full bg-[var(--missio-primary)] px-2 py-1 text-xs font-black text-white">
          {badge}
        </span>
      )}

      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-50 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200">
        {icon}
      </div>

      <span className="text-sm font-black text-[var(--missio-text-main)]">
        {title}
      </span>
    </button>
  )
}

function SummaryMiniCard({
  label,
  value,
}: {
  label: string
  value: string | number
}) {
  return (
    <div className="rounded-2xl bg-white/10 px-3 py-3">
      <p className="text-2xl font-black text-white">{value}</p>
      <p className="mt-1 text-[0.68rem] font-bold leading-4 text-slate-300">
        {label}
      </p>
    </div>
  )
}

function CreateUserSheetContent({
  businessId,
  isTurkish,
  onCreated,
}: {
  businessId: number | null
  isTurkish: boolean
  onCreated: (message: string) => void
}) {
  const [form, setForm] = useState<CreateUserFormState>(emptyCreateUserForm)
  const [isSaving, setIsSaving] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  async function handleCreateUser() {
    if (!businessId) {
      setErrorMessage(isTurkish ? "İşletme bilgisi bulunamadı." : "Business information could not be found.")
      return
    }

    const fullName = form.full_name.trim()
    const username = form.username.trim().toLowerCase()
    const password = form.password.trim()
    const email = normalizeOptionalEmail(form.email)

    if (!fullName || !username || !password) {
      setErrorMessage(isTurkish ? "Ad soyad, kullanıcı adı ve şifre zorunludur." : "Full name, username and password are required.")
      return
    }

    setIsSaving(true)
    setErrorMessage(null)

    try {
      await createBusinessUser(businessId, {
        full_name: fullName,
        username,
        password,
        role: form.role,
        email,
      })

      setForm(emptyCreateUserForm)
      onCreated(isTurkish ? "Kullanıcı oluşturuldu." : "User created.")
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage(isTurkish ? "Kullanıcı oluşturulamadı." : "User could not be created.")
      }
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="space-y-3">
      {errorMessage && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-3 text-sm font-black text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-200">
          {errorMessage}
        </div>
      )}

      <input
        value={form.full_name}
        onChange={(event) => setForm((current) => ({ ...current, full_name: event.target.value }))}
        className="min-h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-[var(--missio-primary)]"
        placeholder={isTurkish ? "Ad soyad" : "Full name"}
      />

      <input
        value={form.username}
        onChange={(event) => setForm((current) => ({ ...current, username: event.target.value }))}
        className="min-h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-[var(--missio-primary)]"
        placeholder={isTurkish ? "Kullanıcı adı" : "Username"}
      />

      <input
        value={form.password}
        onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
        className="min-h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-[var(--missio-primary)]"
        placeholder={isTurkish ? "Geçici şifre" : "Temporary password"}
        type="text"
      />

      <input
        value={form.email}
        onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
        className="min-h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 text-sm font-bold text-[var(--missio-text-main)] outline-none focus:border-[var(--missio-primary)]"
        placeholder={isTurkish ? "E-posta, isteğe bağlı" : "Email, optional"}
        type="email"
      />

      <select
        value={form.role}
        onChange={(event) => setForm((current) => ({ ...current, role: event.target.value as BusinessUserRole }))}
        className="min-h-12 w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 text-sm font-black text-[var(--missio-text-main)] outline-none focus:border-[var(--missio-primary)]"
      >
        <option value="staff">{isTurkish ? "Personel" : "Staff"}</option>
        <option value="manager">{isTurkish ? "Yönetici" : "Manager"}</option>
      </select>

      <button
        type="button"
        onClick={() => void handleCreateUser()}
        disabled={isSaving}
        className="flex min-h-12 w-full items-center justify-center rounded-2xl bg-[var(--missio-primary)] px-4 text-sm font-black text-white shadow-lg shadow-teal-500/20 transition active:scale-95 disabled:opacity-60"
      >
        {isSaving
          ? isTurkish ? "Kaydediliyor..." : "Saving..."
          : isTurkish ? "Kullanıcıyı Kaydet" : "Save User"}
      </button>
    </div>
  )
}

export function BossDashboardPanel({
  businessId,
  currentUser,
  onOpenApprovals,
  onOpenReports,
}: BossDashboardPanelProps) {
  const { language } = useTranslation()
  const isTurkish = language === "tr"
  const todayKey = getLocalTodayDateKey()

  const [tasks, setTasks] = useState<TodayTask[]>([])
  const [closures, setClosures] = useState<DailyOperationClosure[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isTaskAssignOpen, setIsTaskAssignOpen] = useState(false)
  const [isLocationRequestOpen, setIsLocationRequestOpen] = useState(false)
  const [isCreateUserOpen, setIsCreateUserOpen] = useState(false)
  const [isPersonnelOpen, setIsPersonnelOpen] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  async function loadDashboard(
    options: {
      showLoading?: boolean
      showError?: boolean
    } = {},
  ) {
    const showLoading = options.showLoading ?? true
    const showError = options.showError ?? true

    if (!businessId) {
      setTasks([])
      setClosures([])
      setErrorMessage(
        isTurkish
          ? "İşletme bilgisi bulunamadı."
          : "Business information could not be found.",
      )
      return
    }

    if (showLoading) {
      setIsLoading(true)
    }

    if (showError) {
      setErrorMessage(null)
    }

    try {
      const [taskResponse, closureResponse] = await Promise.all([
        listBusinessTasks({
          businessId,
          taskDate: todayKey,
          limit: 500,
          offset: 0,
        }),
        listDailyOperationClosures({
          businessId,
          limit: 10,
          offset: 0,
        }),
      ])

      setTasks(taskResponse.tasks.map(mapApiTaskToTodayTask))
      setClosures(closureResponse.closures)
      setErrorMessage(null)
    } catch (error) {
      if (showError) {
        if (error instanceof Error) {
          setErrorMessage(error.message)
        } else {
          setErrorMessage(
            isTurkish
              ? "Günlük özet alınamadı."
              : "Daily summary could not be loaded.",
          )
        }
      }
    } finally {
      if (showLoading) {
        setIsLoading(false)
      }
    }
  }

  useEffect(() => {
    void loadDashboard()
  }, [businessId])

  useEffect(() => {
    if (!businessId) {
      return
    }

    function refreshDashboardWhenVisible() {
      if (document.visibilityState === "visible") {
        void loadDashboard({
          showLoading: false,
          showError: false,
        })
      }
    }

    const intervalId = window.setInterval(refreshDashboardWhenVisible, 10000)

    window.addEventListener("focus", refreshDashboardWhenVisible)
    document.addEventListener("visibilitychange", refreshDashboardWhenVisible)

    return () => {
      window.clearInterval(intervalId)
      window.removeEventListener("focus", refreshDashboardWhenVisible)
      document.removeEventListener("visibilitychange", refreshDashboardWhenVisible)
    }
  }, [businessId, todayKey])

  const todayClosure = useMemo(
    () => closures.find((closure) => closure.closure_date === todayKey) ?? null,
    [closures, todayKey],
  )

  const completedCount = tasks.filter(isTaskCompletedOrClosed).length
  const approvalWaitingCount = tasks.filter(isApprovalWaiting).length
  const closureStatusText = getClosureStatusText(todayClosure, isTurkish)
  const closureStatusTone = getClosureStatusTone(todayClosure)
  const canManageUsers = currentUser !== undefined && currentUser.business_id !== null

  async function handleTaskCreated() {
    await loadDashboard({
      showLoading: false,
      showError: false,
    })
  }

  return (
    <div className="space-y-4">
      <section className="rounded-[2rem] bg-gradient-to-br from-slate-950 via-slate-900 to-cyan-950 p-4 text-white shadow-xl shadow-slate-950/20">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-black tracking-tight">
              {isTurkish ? "Günlük Özet" : "Daily Summary"}
            </h1>

            <p className="mt-2 max-w-sm text-sm font-bold leading-6 text-slate-300">
              {isTurkish
                ? "Bugünün operasyon durumunu hızlıca kontrol et."
                : "Quickly check today operation status."}
            </p>
          </div>

          <button
            type="button"
            onClick={() => void loadDashboard()}
            disabled={isLoading}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/10 text-cyan-100 transition active:scale-95 disabled:opacity-60"
            aria-label={isTurkish ? "Yenile" : "Refresh"}
          >
            <RefreshCw className={isLoading ? "animate-spin" : ""} size={19} />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <SummaryMiniCard
            label={isTurkish ? "Bugünkü görev" : "Today tasks"}
            value={tasks.length}
          />

          <SummaryMiniCard
            label={isTurkish ? "Tamamlanan" : "Completed"}
            value={completedCount}
          />

          <SummaryMiniCard
            label={isTurkish ? "Bekleyen onay" : "Pending approval"}
            value={approvalWaitingCount}
          />

          <div className="rounded-2xl bg-white/10 px-3 py-3">
            <p className={`inline-flex rounded-full px-2.5 py-1 text-xs font-black ${closureStatusTone}`}>
              {closureStatusText}
            </p>
            <p className="mt-2 text-[0.68rem] font-bold leading-4 text-slate-300">
              {isTurkish ? "Gün kapanışı" : "Daily closing"}
            </p>
          </div>
        </div>
      </section>

      {errorMessage && (
        <div className="rounded-[1.35rem] border border-rose-200 bg-rose-50 p-3 text-sm font-black text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
          {errorMessage}
        </div>
      )}

      {successMessage && (
        <div className="rounded-[1.35rem] border border-emerald-200 bg-emerald-50 p-3 text-sm font-black text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200">
          {successMessage}
        </div>
      )}

      <section className="space-y-3">
        <div className="flex items-center justify-between gap-3 px-1">
          <div>
<h2 className="mt-1 text-lg font-black text-[var(--missio-text-main)]">
              {isTurkish ? "Hızlı İşlemler" : "Quick Actions"}
            </h2>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <QuickActionCard
            title={isTurkish ? "Görev Ata" : "Assign Task"}
            icon={<PlusSquare size={24} />}
            onClick={() => {
              setSuccessMessage(null)
              setIsTaskAssignOpen(true)
            }}
          />

          <QuickActionCard
            title={isTurkish ? "Konum İste" : "Request Location"}
            icon={<MapPin size={24} />}
            onClick={() => {
              setSuccessMessage(null)
              setIsLocationRequestOpen(true)
            }}
          />

          {canManageUsers && (
            <QuickActionCard
              title={isTurkish ? "Kullanıcı Ekle" : "Add User"}
              icon={<UserPlus size={24} />}
              onClick={() => {
                setSuccessMessage(null)
                setIsCreateUserOpen(true)
              }}
            />
          )}

          <QuickActionCard
            title={isTurkish ? "Onaylar" : "Approvals"}
            icon={<ClipboardCheck size={24} />}
            badge={approvalWaitingCount > 0 ? approvalWaitingCount : null}
            onClick={onOpenApprovals}
          />

          <QuickActionCard
            title={isTurkish ? "Raporlar" : "Reports"}
            icon={<BarChart3 size={24} />}
            onClick={onOpenReports}
          />

          {canManageUsers && (
            <QuickActionCard
              title={isTurkish ? "Personel" : "Personnel"}
              icon={<UsersRound size={24} />}
              onClick={() => {
                setSuccessMessage(null)
                setIsPersonnelOpen(true)
              }}
            />
          )}
        </div>
      </section>

      <TaskAssignSheet
        businessId={businessId}
        isOpen={isTaskAssignOpen}
        assignableRoles={["staff", "manager"]}
        defaultRequiresManagerApproval={false}
        allowLocationRequirement
        onClose={() => setIsTaskAssignOpen(false)}
        onCreated={handleTaskCreated}
        onSuccess={setSuccessMessage}
      />

      <ActionSheet
        isOpen={isLocationRequestOpen}
        title={isTurkish ? "Konum İste" : "Request Location"}
        onClose={() => setIsLocationRequestOpen(false)}
      >
        <LocationCheckRequestPanel businessId={businessId} />
      </ActionSheet>

      <ActionSheet
        isOpen={isCreateUserOpen}
        title={isTurkish ? "Kullanıcı Ekle" : "Add User"}
        onClose={() => setIsCreateUserOpen(false)}
      >
        <CreateUserSheetContent
          businessId={businessId}
          isTurkish={isTurkish}
          onCreated={(message) => {
            setSuccessMessage(message)
            setIsCreateUserOpen(false)
          }}
        />
      </ActionSheet>

      {currentUser && (
        <ActionSheet
          isOpen={isPersonnelOpen}
          title={isTurkish ? "Personel" : "Personnel"}
          onClose={() => setIsPersonnelOpen(false)}
        >
          <BilingualUserManagementPanel currentUser={currentUser} />
        </ActionSheet>
      )}
    </div>
  )
}