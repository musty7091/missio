import { AlertCircle, BarChart3, Bell, ClipboardCheck, UserRound } from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import { LoginScreen } from "./components/auth/LoginScreen"
import {
  AppStatePanel,
  FullScreenStatus,
  TaskLoadingSkeleton,
} from "./components/common/AppStatePanel"
import { AppHeader } from "./components/layout/AppHeader"
import { BottomNavigation, type AppTab } from "./components/layout/BottomNavigation"
import { ProfilePanel } from "./components/profile/ProfilePanel"
import { TaskCard } from "./components/tasks/TaskCard"
import { TaskDetailPanel } from "./components/tasks/TaskDetailPanel"
import { TaskSectionHeader } from "./components/tasks/TaskSectionHeader"
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
  const [activeTab, setActiveTab] = useState<AppTab>("tasks")
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null)
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

    void loadTodayTasks()
  }, [currentUser])

  const selectedTask = useMemo(() => {
    if (!selectedTaskId) {
      return null
    }

    return tasks.find((task) => task.id === selectedTaskId) ?? null
  }, [selectedTaskId, tasks])

  const taskStats = useMemo(() => {
    return {
      totalCount: tasks.length,
      completedCount: tasks.filter(
        (task) => task.status === "completed" || task.status === "approved",
      ).length,
      waitingCount: tasks.filter((task) => task.status === "assigned").length,
      activeCount: tasks.filter((task) => task.status === "in_progress").length,
      remainingCount: tasks.filter(
        (task) => task.status !== "completed" && task.status !== "approved",
      ).length,
      routineCount: tasks.filter((task) => task.taskType === "routine").length,
      extraCount: tasks.filter((task) => task.taskType === "extra").length,
    }
  }, [tasks])

  function handleLogout() {
    clearAccessToken()
    setCurrentUser(null)
    setTasks([])
    setSelectedTaskId(null)
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

  async function handleCompleteTask(task: TodayTask) {
    setBusyTaskId(task.id)
    setTasksErrorMessage(null)

    try {
      const locationPayload = await getLocationPayloadForTask(task)
      await completeTask(task.id, locationPayload)
      await loadTodayTasks()
    } catch (error) {
      if (error instanceof Error) {
        setTasksErrorMessage(error.message)
      } else {
        setTasksErrorMessage("Görev tamamlanamadı.")
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

        {activeTab === "tasks" ? (
          <>
            <TodayOperationSummary
              totalCount={taskStats.totalCount}
              completedCount={taskStats.completedCount}
              activeCount={taskStats.activeCount}
              waitingCount={taskStats.waitingCount}
              remainingCount={taskStats.remainingCount}
            />

            <TaskSectionHeader
              totalCount={taskStats.totalCount}
              routineCount={taskStats.routineCount}
              extraCount={taskStats.extraCount}
            />

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
                tasks.map((task) => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    isBusy={busyTaskId === task.id}
                    onOpenDetails={(task) => setSelectedTaskId(task.id)}
                  />
                ))}
            </section>
          </>
        ) : activeTab === "profile" ? (
          <ProfilePanel
            user={currentUser}
            theme={theme}
            onToggleTheme={() => setTheme(theme === "light" ? "dark" : "light")}
            onLogout={handleLogout}
          />
        ) : (
          <ComingSoonPanel tab={activeTab} />
        )}

        {selectedTask && (
          <TaskDetailPanel
            task={selectedTask}
            isBusy={busyTaskId === selectedTask.id}
            onClose={() => setSelectedTaskId(null)}
            onStartTask={handleStartTask}
            onCompleteTask={handleCompleteTask}
            onUploadPhoto={handleUploadPhoto}
          />
        )}

        <BottomNavigation activeTab={activeTab} onTabChange={setActiveTab} />
      </section>
    </main>
  )
}

