import {
  AlertCircle,
  BarChart3,
  Bell,
  CalendarClock,
  ClipboardCheck,
  LockKeyhole,
  PhoneCall,
  UserRound,
} from "lucide-react"
import { useEffect, useMemo, useRef, useState } from "react"
import { ApprovalsPanel } from "./components/approvals/ApprovalsPanel"
import { LoginScreen } from "./components/auth/LoginScreen"
import {
  AppStatePanel,
  FullScreenStatus,
  TaskLoadingSkeleton,
} from "./components/common/AppStatePanel"
import { AppHeader } from "./components/layout/AppHeader"
import { BottomNavigation, type AppTab } from "./components/layout/BottomNavigation"
import { BossDashboardPanel } from "./components/boss/BossDashboardPanel"
import { BossReportsPanel } from "./components/boss/BossReportsPanel"
import { ManagerTasksPanel } from "./components/manager/ManagerTasksPanel"
import { NotificationPanel } from "./components/notifications/NotificationPanel"
import { ProfilePanel } from "./components/profile/ProfilePanel"
import { ReportsPanel } from "./components/reports/ReportsPanel"
import { SuperAdminBusinessesPanel } from "./components/super-admin/SuperAdminBusinessesPanel"
import { TaskCard } from "./components/tasks/TaskCard"
import { TaskDetailPanel } from "./components/tasks/TaskDetailPanel"
import { TaskFilterTabs, type TaskListFilter } from "./components/tasks/TaskFilterTabs"
import { TaskGroupHeader } from "./components/tasks/TaskGroupHeader"
import { TodayOperationSummary } from "./components/tasks/TodayOperationSummary"
import { getCurrentUser } from "./services/authService"
import { clearAccessToken, getAccessToken } from "./services/authTokenStorage"
import {
  completeTask,
  getMyTodayTasks,
  startTask,
  uploadTaskAttachment,
} from "./services/taskService"
import type { UserMeResponse } from "./types/auth"
import type { ThemeMode, TodayTask } from "./types/task"
import { mapMyTodayTasksResponseToTodayTasks } from "./utils/apiTaskMapper"

type LocationPayload = {
  latitude?: number | null
  longitude?: number | null
  location_accuracy?: number | null
}

type ComingSoonPanelProps = {
  tab: Exclude<AppTab, "tasks">
}

function getCurrentLocationPayload(): Promise<LocationPayload> {
  return new Promise((resolve, reject) => {
    if (!("geolocation" in navigator)) {
      reject(new Error("Bu cihazda konum desteği bulunamadı."))
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          location_accuracy: position.coords.accuracy,
        })
      },
      () => {
        reject(new Error("Konum izni alınamadı. Lütfen tarayıcı konum iznini kontrol edin."))
      },
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 30000,
      },
    )
  })
}

async function getLocationPayloadForTask(task: TodayTask): Promise<LocationPayload> {
  if (!task.requiresLocation) {
    return {}
  }

  return getCurrentLocationPayload()
}

function getBottomNotificationCount(tasks: TodayTask[]) {
  let count = 0

  if (tasks.some((task) => task.taskType === "routine" && task.status === "assigned")) {
    count += 1
  }

  if (tasks.some((task) => task.taskType === "extra" && task.status === "assigned")) {
    count += 1
  }

  if (tasks.some((task) => task.status === "in_progress")) {
    count += 1
  }

  if (
    tasks.some(
      (task) =>
        task.requiresPhoto &&
        task.status !== "completed" &&
        task.status !== "approved" &&
        task.status !== "cancelled",
    )
  ) {
    count += 1
  }

  if (
    tasks.some(
      (task) => task.status === "completed" && task.requiresManagerApproval,
    )
  ) {
    count += 1
  }

  return count
}

function ComingSoonPanel({ tab }: ComingSoonPanelProps) {
  const panelInfo = {
    notifications: {
      eyebrow: "Bildirim merkezi",
      title: "Bildirimler hazırlanıyor",
      description:
        "Görev atama, onay, ret ve gün sonu uyarıları burada toplanacak.",
      icon: Bell,
    },
    reports: {
      eyebrow: "Operasyon raporları",
      title: "Raporlar hazırlanıyor",
      description:
        "Günlük görev performansı, eksik işler ve personel özeti bu ekranda gösterilecek.",
      icon: BarChart3,
    },
    profile: {
      eyebrow: "Kullanıcı profili",
      title: "Profil hazırlanıyor",
      description:
        "Kullanıcı bilgileri, rol, tema tercihi ve hesap ayarları burada yer alacak.",
      icon: UserRound,
    },
  }[tab]

  const Icon = panelInfo.icon

  return (
    <section className="flex flex-1 flex-col pb-24">
      <AppStatePanel
        icon={<Icon size={30} />}
        eyebrow={panelInfo.eyebrow}
        title={panelInfo.title}
        description={panelInfo.description}
      />
    </section>
  )
}


const SUPPORT_PHONE_DISPLAY = "0533 880 11 43"
const SUPPORT_PHONE_HREF = "tel:+905338801143"


function formatSubscriptionLockDate(value: string | null) {
  if (!value) {
    return "Bitiş tarihi bulunamadı"
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return "Bitiş tarihi okunamadı"
  }

  return date.toLocaleString("tr-TR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function isBossSubscriptionLockView(user: UserMeResponse) {
  return user.role === "boss"
}

function getSubscriptionLockTitle(user: UserMeResponse) {
  if (!isBossSubscriptionLockView(user)) {
    return "Sistem geçici olarak kullanıma kapalı"
  }

  if (user.subscription_access_status === "expired_locked") {
    return "Abonelik süresi doldu"
  }

  if (user.subscription_lock_reason === "subscription_suspended") {
    return "Abonelik askıya alındı"
  }

  if (user.subscription_lock_reason === "subscription_cancelled") {
    return "Abonelik iptal edildi"
  }

  return "Abonelik erişimi kısıtlandı"
}

function getSubscriptionLockDescription(user: UserMeResponse) {
  if (!isBossSubscriptionLockView(user)) {
    return "Şu anda işletme hesabı geçici olarak kullanıma kapalıdır. Lütfen işletme yöneticinizle iletişime geçin."
  }

  if (user.subscription_access_status === "expired_locked") {
    return "Uygulamaya giriş yaptın ancak abonelik süresi dolduğu için görev, onay ve rapor işlemleri geçici olarak kapatıldı."
  }

  return "Bu işletmenin abonelik durumu aktif olmadığı için operasyon işlemleri geçici olarak kapatıldı."
}

function SubscriptionLockedPanel({
  user,
  onLogout,
}: {
  user: UserMeResponse
  onLogout: () => void
}) {
  const showBossSubscriptionDetails = isBossSubscriptionLockView(user)

  return (
    <section className="flex flex-1 flex-col pb-24">
      <div className="rounded-[1.8rem] border border-amber-200 bg-amber-50 p-5 shadow-sm dark:border-amber-900 dark:bg-amber-950/30">
        <div className="mb-4 flex items-start gap-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-100">
            <LockKeyhole size={25} />
          </div>

          <div className="min-w-0">
            <p className="text-[0.68rem] font-black uppercase tracking-[0.18em] text-amber-700 dark:text-amber-200">
              {showBossSubscriptionDetails ? "Abonelik uyarısı" : "Sistem uyarısı"}
            </p>
            <h1 className="mt-1 text-2xl font-black text-amber-950 dark:text-amber-50">
              {getSubscriptionLockTitle(user)}
            </h1>
            <p className="mt-2 text-sm font-bold leading-6 text-amber-800 dark:text-amber-100">
              {getSubscriptionLockDescription(user)}
            </p>
          </div>
        </div>

        {showBossSubscriptionDetails ? (
          <>
            <div className="rounded-[1.35rem] border border-amber-200 bg-white/70 p-4 text-sm font-bold leading-6 text-amber-950 dark:border-amber-900 dark:bg-slate-950/40 dark:text-amber-100">
              <div className="mb-2 flex items-center gap-2">
                <CalendarClock size={18} />
                <p className="font-black">Abonelik bilgisi</p>
              </div>

              <p>Durum: {user.subscription_status ?? "Bilinmiyor"}</p>
              <p>Bitiş: {formatSubscriptionLockDate(user.subscription_ends_at_utc)}</p>
              <p>
                Kalan gün:{" "}
                {user.subscription_is_expired
                  ? "Süre doldu"
                  : user.subscription_remaining_days ?? "-"}
              </p>
            </div>

            <a
              href={SUPPORT_PHONE_HREF}
              className="mt-4 flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-emerald-600 px-4 text-sm font-black text-white shadow-sm"
            >
              <PhoneCall size={18} />
              Destek için ara: {SUPPORT_PHONE_DISPLAY}
            </a>

            <div className="mt-4 rounded-[1.35rem] border border-amber-200 bg-white/70 p-4 text-sm font-bold leading-6 text-amber-950 dark:border-amber-900 dark:bg-slate-950/40 dark:text-amber-100">
              <p className="font-black">Kapatılan işlemler</p>
              <p className="mt-1">Görev oluşturma, görev tamamlama, fotoğraf yükleme, onay ve rapor işlemleri çalışmaz.</p>
              <p className="mt-1">Abonelik yenilendiğinde sistem tekrar normal kullanıma açılır.</p>
            </div>
          </>
        ) : (
          <div className="rounded-[1.35rem] border border-amber-200 bg-white/70 p-4 text-sm font-bold leading-6 text-amber-950 dark:border-amber-900 dark:bg-slate-950/40 dark:text-amber-100">
            <p className="font-black">Bilgilendirme</p>
            <p className="mt-1">
              Görev ve operasyon ekranları geçici olarak kullanılamıyor.
            </p>
            <p className="mt-1">
              Bu durumla ilgili işletme sahibi veya yetkili yöneticinizle iletişime geçin.
            </p>
          </div>
        )}

        <button
          type="button"
          onClick={onLogout}
          className="mt-4 flex min-h-12 w-full items-center justify-center rounded-2xl bg-amber-600 px-4 text-sm font-black text-white shadow-sm"
        >
          Çıkış yap
        </button>
      </div>
    </section>
  )
}


export default function App() {
  const [theme, setTheme] = useState<ThemeMode>(() => {
    const savedTheme = window.localStorage.getItem("missio-theme")

    if (savedTheme === "light" || savedTheme === "dark") {
      return savedTheme
    }

    if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
      return "dark"
    }

    return "light"
  })

  const [currentUser, setCurrentUser] = useState<UserMeResponse | null>(null)
  const [isCheckingSession, setIsCheckingSession] = useState(() => Boolean(getAccessToken()))
  const [activeTab, setActiveTab] = useState<AppTab>(() => {
    const savedTab = window.localStorage.getItem("missio-active-tab")

    if (
      savedTab === "tasks" ||
      savedTab === "notifications" ||
      savedTab === "reports" ||
      savedTab === "profile"
    ) {
      return savedTab
    }

    return "tasks"
  })
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null)
  const taskDetailHistoryTokenRef = useRef<string | null>(null)
  const [taskListFilter, setTaskListFilter] = useState<TaskListFilter>("all")
  const [tasks, setTasks] = useState<TodayTask[]>([])
  const [isLoadingTasks, setIsLoadingTasks] = useState(false)
  const [tasksErrorMessage, setTasksErrorMessage] = useState<string | null>(null)
  const [busyTaskId, setBusyTaskId] = useState<number | null>(null)

  useEffect(() => {
    const root = document.documentElement

    if (theme === "dark") {
      root.classList.add("dark")
    } else {
      root.classList.remove("dark")
    }

    window.localStorage.setItem("missio-theme", theme)
  }, [theme])

  useEffect(() => {
    window.localStorage.setItem("missio-active-tab", activeTab)
  }, [activeTab])

  useEffect(() => {
    const token = getAccessToken()

    if (!token) {
      setIsCheckingSession(false)
      return
    }

    getCurrentUser()
      .then((user) => {
        setCurrentUser(user)
      })
      .catch(() => {
        clearAccessToken()
        setCurrentUser(null)
      })
      .finally(() => {
        setIsCheckingSession(false)
      })
  }, [])

  async function loadTodayTasks() {
    setIsLoadingTasks(true)
    setTasksErrorMessage(null)

    try {
      const response = await getMyTodayTasks()
      setTasks(mapMyTodayTasksResponseToTodayTasks(response))
    } catch (error) {
      if (error instanceof Error) {
        setTasksErrorMessage(error.message)
      } else {
        setTasksErrorMessage("Bugünkü görevler alınamadı.")
      }

      setTasks([])
    } finally {
      setIsLoadingTasks(false)
    }
  }

  useEffect(() => {
    if (!currentUser) {
      setTasks([])
      setTasksErrorMessage(null)
      return
    }

    if (currentUser.role === "super_admin") {
      setTasks([])
      setTasksErrorMessage(null)
      return
    }

    if (currentUser.subscription_access_status !== "active") {
      setTasks([])
      setTasksErrorMessage(null)
      return
    }

    void loadTodayTasks()
  }, [currentUser])

  const selectedTask = useMemo(() => {
    if (selectedTaskId === null) {
      return null
    }

    return tasks.find((task) => task.id === selectedTaskId) ?? null
  }, [selectedTaskId, tasks])

  function openTaskDetails(task: TodayTask) {
    const historyToken = `missio-task-detail-${task.id}-${Date.now()}`
    taskDetailHistoryTokenRef.current = historyToken

    window.history.pushState(
      {
        ...(window.history.state ?? {}),
        missioTaskDetailToken: historyToken,
      },
      "",
      window.location.href,
    )

    setSelectedTaskId(task.id)
  }

  function closeTaskDetails() {
    if (
      selectedTaskId !== null &&
      taskDetailHistoryTokenRef.current !== null &&
      window.history.state?.missioTaskDetailToken === taskDetailHistoryTokenRef.current
    ) {
      window.history.back()
      return
    }

    taskDetailHistoryTokenRef.current = null
    setSelectedTaskId(null)
  }

  useEffect(() => {
    function handleBrowserBack(event: PopStateEvent) {
      if (selectedTaskId === null) {
        return
      }

      const stillInsideTaskDetail =
        taskDetailHistoryTokenRef.current !== null &&
        event.state?.missioTaskDetailToken === taskDetailHistoryTokenRef.current

      if (stillInsideTaskDetail) {
        return
      }

      taskDetailHistoryTokenRef.current = null
      setSelectedTaskId(null)
    }

    window.addEventListener("popstate", handleBrowserBack)

    return () => {
      window.removeEventListener("popstate", handleBrowserBack)
    }
  }, [selectedTaskId])

  const taskStats = useMemo(() => {
    const completedCount = tasks.filter(
      (task) => task.status === "completed" || task.status === "approved",
    ).length

    const rejectedCount = tasks.filter((task) => task.status === "rejected").length

    return {
      totalCount: tasks.length,
      completedCount,
      rejectedCount,
      waitingCount: tasks.filter(
        (task) => task.status === "assigned" || task.status === "rejected",
      ).length,
      activeCount: tasks.filter((task) => task.status === "in_progress").length,
      remainingCount: tasks.filter(
        (task) => task.status !== "completed" && task.status !== "approved",
      ).length,
    }
  }, [tasks])

  const filteredTasks = useMemo(() => {
    if (taskListFilter === "waiting") {
      return tasks.filter(
        (task) => task.status === "assigned" || task.status === "rejected",
      )
    }

    if (taskListFilter === "active") {
      return tasks.filter((task) => task.status === "in_progress")
    }

    if (taskListFilter === "completed") {
      return tasks.filter((task) => task.status === "completed" || task.status === "approved")
    }

    return tasks
  }, [taskListFilter, tasks])

  const routineFilteredTasks = useMemo(() => {
    return filteredTasks.filter((task) => task.taskType === "routine")
  }, [filteredTasks])

  const extraFilteredTasks = useMemo(() => {
    return filteredTasks.filter((task) => task.taskType === "extra")
  }, [filteredTasks])


  const bottomNotificationCount = useMemo(() => getBottomNotificationCount(tasks), [tasks])

  function handleLogout() {
    clearAccessToken()
    setCurrentUser(null)
    setTasks([])
    setSelectedTaskId(null)
    taskDetailHistoryTokenRef.current = null
    setTaskListFilter("all")
    window.localStorage.setItem("missio-active-tab", "tasks")
    setActiveTab("tasks")
  }

  async function handleStartTask(task: TodayTask) {
    setBusyTaskId(task.id)
    setTasksErrorMessage(null)

    try {
      const locationPayload = await getLocationPayloadForTask(task)
      await startTask(task.id, locationPayload)
      await loadTodayTasks()
    } catch (error) {
      if (error instanceof Error) {
        setTasksErrorMessage(error.message)
      } else {
        setTasksErrorMessage("Görev başlatılamadı.")
      }
    } finally {
      setBusyTaskId(null)
    }
  }

  async function handleCompleteTask(task: TodayTask, note?: string) {
    setBusyTaskId(task.id)
    setTasksErrorMessage(null)

    try {
      const locationPayload = await getLocationPayloadForTask(task)
      await completeTask(task.id, {
        ...locationPayload,
        note: note?.trim() || null,
      })
      await loadTodayTasks()
    } catch (error) {
      if (error instanceof Error) {
        setTasksErrorMessage(error.message)
        throw error
      } else {
        const fallbackError = new Error("Görev tamamlanamadı.")
        setTasksErrorMessage(fallbackError.message)
        throw fallbackError
      }
    } finally {
      setBusyTaskId(null)
    }
  }

  async function handleUploadPhoto(task: TodayTask, file: File) {
    setBusyTaskId(task.id)
    setTasksErrorMessage(null)

    try {
      const locationPayload = task.requiresLocation ? await getCurrentLocationPayload() : {}
      await uploadTaskAttachment(task.id, {
        file,
        ...locationPayload,
      })
      await loadTodayTasks()
    } catch (error) {
      if (error instanceof Error) {
        setTasksErrorMessage(error.message)
      } else {
        setTasksErrorMessage("Fotoğraf yüklenemedi.")
      }
    } finally {
      setBusyTaskId(null)
    }
  }

  if (isCheckingSession) {
    return (
      <FullScreenStatus
        title="Missio hazırlanıyor"
        description="Oturum bilgilerin kontrol ediliyor."
      />
    )
  }

  if (!currentUser) {
    return (
      <LoginScreen
        theme={theme}
        onToggleTheme={() => setTheme(theme === "light" ? "dark" : "light")}
        onLoginSuccess={setCurrentUser}
      />
    )
  }

  const isTenantSubscriptionLocked =
    currentUser.business_id !== null &&
    currentUser.role !== "super_admin" &&
    currentUser.subscription_access_status !== "active"

  return (
    <main className="min-h-screen bg-[var(--missio-page-bg)] px-4 py-5 text-[var(--missio-text-main)] transition-colors duration-300">
      <section className="mx-auto flex min-h-[calc(100vh-40px)] w-full max-w-md flex-col">
        <AppHeader
          theme={theme}
          displayName={currentUser.full_name}
          role={currentUser.role}
          onToggleTheme={() => setTheme(theme === "light" ? "dark" : "light")}
          onLogout={handleLogout}
        />

        {isTenantSubscriptionLocked ? (
          <SubscriptionLockedPanel
            user={currentUser}
            onLogout={handleLogout}
          />
        ) : activeTab === "tasks" ? (
          currentUser.role === "super_admin" ? (
            <SuperAdminBusinessesPanel />
          ) : currentUser.role === "staff" ? (
            <>
            <TodayOperationSummary
              totalCount={taskStats.totalCount}
              completedCount={taskStats.completedCount}
              activeCount={taskStats.activeCount}
              waitingCount={taskStats.waitingCount}
              rejectedCount={taskStats.rejectedCount}
              remainingCount={taskStats.remainingCount}
            />

            {tasks.length > 0 && (
              <TaskFilterTabs
                activeFilter={taskListFilter}
                tasks={tasks}
                onFilterChange={setTaskListFilter}
              />
            )}

            <section className="flex flex-1 flex-col gap-2.5 pb-24">
              {isLoadingTasks && <TaskLoadingSkeleton />}

              {!isLoadingTasks && tasksErrorMessage && (
                <AppStatePanel
                  icon={<AlertCircle size={30} />}
                  eyebrow="Görev ekranı"
                  title="Görevler alınamadı"
                  description={tasksErrorMessage}
                  tone="error"
                  actionLabel="Tekrar dene"
                  onAction={() => void loadTodayTasks()}
                />
              )}

              {!isLoadingTasks && !tasksErrorMessage && tasks.length === 0 && (
                <AppStatePanel
                  icon={<ClipboardCheck size={30} />}
                  eyebrow="Bugünün görevleri"
                  title="Bugün atanmış görev yok"
                  description="Yeni görev atandığında burada görünecek."
                />
              )}

              {!isLoadingTasks &&
                !tasksErrorMessage &&
                tasks.length > 0 &&
                filteredTasks.length === 0 && (
                  <AppStatePanel
                    icon={<ClipboardCheck size={30} />}
                    eyebrow="Görev filtresi"
                    title="Bu filtrede görev yok"
                    description="Başka bir filtre seçerek diğer görevleri görüntüleyebilirsin."
                  />
                )}

              {!isLoadingTasks &&
                !tasksErrorMessage &&
                routineFilteredTasks.length > 0 && (
                  <>
                    <TaskGroupHeader type="routine" count={routineFilteredTasks.length} />

                    {routineFilteredTasks.map((task) => (
                      <TaskCard
                        key={task.id}
                        task={task}
                        isBusy={busyTaskId === task.id}
                        onOpenDetails={openTaskDetails}
                      />
                    ))}
                  </>
                )}

              {!isLoadingTasks &&
                !tasksErrorMessage &&
                extraFilteredTasks.length > 0 && (
                  <>
                    <TaskGroupHeader type="extra" count={extraFilteredTasks.length} />

                    {extraFilteredTasks.map((task) => (
                      <TaskCard
                        key={task.id}
                        task={task}
                        isBusy={busyTaskId === task.id}
                        onOpenDetails={openTaskDetails}
                      />
                    ))}
                  </>
                )}
            </section>
          </>
          ) : currentUser.role === "boss" ? (
            <BossDashboardPanel
              businessId={currentUser.business_id}
              onOpenApprovals={() => setActiveTab("notifications")}
              onOpenReports={() => setActiveTab("reports")}
            />
          ) : (
            <ManagerTasksPanel
              businessId={currentUser.business_id}
              currentUserId={currentUser.id}
              busyTaskId={busyTaskId}
              onOpenOwnTaskDetails={openTaskDetails}
              onChanged={() => void loadTodayTasks()}
            />
          )
        ) : activeTab === "notifications" ? (
          currentUser.role === "super_admin" ? (
            <ComingSoonPanel tab="notifications" />
          ) : currentUser.role === "staff" ? (
            <NotificationPanel
              tasks={tasks}
              onOpenTaskDetails={openTaskDetails}
            />
          ) : (
            <ApprovalsPanel
              businessId={currentUser.business_id}
              onChanged={() => void loadTodayTasks()}
            />
          )
        ) : activeTab === "reports" ? (
          currentUser.role === "super_admin" ? (
            <ComingSoonPanel tab="reports" />
          ) : currentUser.role === "boss" ? (
            <BossReportsPanel businessId={currentUser.business_id} />
          ) : (
            <ReportsPanel
              tasks={tasks}
              role={currentUser.role}
              businessId={currentUser.business_id}
              onOpenTaskDetails={openTaskDetails}
            />
          )
        ) : activeTab === "profile" ? (
          <ProfilePanel
            user={currentUser}
            theme={theme}
            onToggleTheme={() => setTheme(theme === "light" ? "dark" : "light")}
            onLogout={handleLogout}
            onProfileUpdated={setCurrentUser}
          />
        ) : (
          <ComingSoonPanel tab={activeTab} />
        )}

        {!isTenantSubscriptionLocked && selectedTask && (
          <TaskDetailPanel
            task={selectedTask}
            isBusy={busyTaskId === selectedTask.id}
            onClose={closeTaskDetails}
            onStartTask={handleStartTask}
            onCompleteTask={handleCompleteTask}
            onUploadPhoto={handleUploadPhoto}
          />
        )}

        {!isTenantSubscriptionLocked && (
          <BottomNavigation
            activeTab={activeTab}
            notificationCount={bottomNotificationCount}
            role={currentUser.role}
            onTabChange={setActiveTab}
          />
        )}
      </section>
    </main>
  )
}












