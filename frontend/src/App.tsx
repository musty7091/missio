import { useEffect, useMemo, useState } from "react"
import { LoginScreen } from "./components/auth/LoginScreen"
import { AppHeader } from "./components/layout/AppHeader"
import { BottomNavigation } from "./components/layout/BottomNavigation"
import { TaskCard } from "./components/tasks/TaskCard"
import { TaskSectionHeader } from "./components/tasks/TaskSectionHeader"
import { TodayOperationSummary } from "./components/tasks/TodayOperationSummary"
import { todayTasks } from "./data/todayTasks"
import { getCurrentUser } from "./services/authService"
import { clearAccessToken, getAccessToken } from "./services/authTokenStorage"
import type { UserMeResponse } from "./types/auth"
import type { ThemeMode } from "./types/task"

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

  const taskStats = useMemo(() => {
    return {
      totalCount: todayTasks.length,
      completedCount: todayTasks.filter((task) => task.status === "completed").length,
      waitingCount: todayTasks.filter((task) => task.status === "assigned").length,
      activeCount: todayTasks.filter((task) => task.status === "in_progress").length,
    }
  }, [])

  function handleLogout() {
    clearAccessToken()
    setCurrentUser(null)
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

        <section className="flex flex-1 flex-col gap-4 pb-24">
          {todayTasks.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </section>

        <BottomNavigation />
      </section>
    </main>
  )
}
