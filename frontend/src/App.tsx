import { AlertCircle } from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import { LoginScreen } from "./components/auth/LoginScreen"
import { AppHeader } from "./components/layout/AppHeader"
import { BottomNavigation } from "./components/layout/BottomNavigation"
import { TaskCard } from "./components/tasks/TaskCard"
import { TaskSectionHeader } from "./components/tasks/TaskSectionHeader"
import { TodayOperationSummary } from "./components/tasks/TodayOperationSummary"
import { getCurrentUser } from "./services/authService"
import { clearAccessToken, getAccessToken } from "./services/authTokenStorage"
import { getMyTodayTasks } from "./services/taskService"
import type { UserMeResponse } from "./types/auth"
import type { ThemeMode, TodayTask } from "./types/task"
import { mapMyTodayTasksResponseToTodayTasks } from "./utils/apiTaskMapper"

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
  const [tasks, setTasks] = useState<TodayTask[]>([])
  const [isLoadingTasks, setIsLoadingTasks] = useState(false)
  const [tasksErrorMessage, setTasksErrorMessage] = useState<string | null>(null)

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

  useEffect(() => {
    if (!currentUser) {
      setTasks([])
      setTasksErrorMessage(null)
      return
    }

    setIsLoadingTasks(true)
    setTasksErrorMessage(null)

    getMyTodayTasks()
      .then((response) => {
        setTasks(mapMyTodayTasksResponseToTodayTasks(response))
      })
      .catch((error) => {
        if (error instanceof Error) {
          setTasksErrorMessage(error.message)
        } else {
          setTasksErrorMessage("Bugünkü görevler alınamadı.")
        }

        setTasks([])
      })
      .finally(() => {
        setIsLoadingTasks(false)
      })
  }, [currentUser])

  const taskStats = useMemo(() => {
    return {
      totalCount: tasks.length,
      completedCount: tasks.filter((task) => task.status === "completed" || task.status === "approved").length,
      waitingCount: tasks.filter((task) => task.status === "assigned").length,
      activeCount: tasks.filter((task) => task.status === "in_progress").length,
    }
  }, [tasks])

  function handleLogout() {
    clearAccessToken()
    setCurrentUser(null)
    setTasks([])
  }

  if (isCheckingSession) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--missio-page-bg)] px-4 text-[var(--missio-text-main)]">
        <div className="rounded-[2rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-6 text-center shadow-xl shadow-slate-900/5">
          <p className="text-sm font-bold text-[var(--missio-text-muted)]">Missio hazırlanıyor...</p>
          <h1 className="mt-2 text-2xl font-black">Oturum kontrol ediliyor</h1>
        </div>
      </main>
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
          onToggleTheme={() => setTheme(theme === "light" ? "dark" : "light")}
          onLogout={handleLogout}
        />

        <TodayOperationSummary
          totalCount={taskStats.totalCount}
          completedCount={taskStats.completedCount}
          activeCount={taskStats.activeCount}
          waitingCount={taskStats.waitingCount}
        />

        <TaskSectionHeader />

        {tasksErrorMessage && (
          <div className="mb-4 flex items-start gap-3 rounded-[1.5rem] border border-red-200 bg-red-50 p-4 text-sm font-semibold text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
            <AlertCircle className="mt-0.5 shrink-0" size={18} />
            <p>{tasksErrorMessage}</p>
          </div>
        )}

        <section className="flex flex-1 flex-col gap-4 pb-24">
          {isLoadingTasks && (
            <div className="rounded-[1.75rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-5 shadow-sm">
              <p className="text-sm font-bold text-[var(--missio-text-muted)]">Görevler yükleniyor...</p>
              <div className="mt-4 space-y-3">
                <div className="h-4 w-3/4 rounded-full bg-slate-200 dark:bg-slate-800" />
                <div className="h-4 w-1/2 rounded-full bg-slate-200 dark:bg-slate-800" />
                <div className="h-10 w-full rounded-2xl bg-slate-200 dark:bg-slate-800" />
              </div>
            </div>
          )}

          {!isLoadingTasks && !tasksErrorMessage && tasks.length === 0 && (
            <div className="rounded-[1.75rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-5 text-center shadow-sm">
              <p className="text-lg font-black">Bugün atanmış görev yok.</p>
              <p className="mt-2 text-sm leading-6 text-[var(--missio-text-muted)]">
                Yeni görev atandığında burada görünecek.
              </p>
            </div>
          )}

          {!isLoadingTasks &&
            tasks.map((task) => (
              <TaskCard key={task.id} task={task} />
            ))}
        </section>

        <BottomNavigation />
      </section>
    </main>
  )
}
