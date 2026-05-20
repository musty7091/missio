import { useEffect, useMemo, useState } from "react"
import { AppHeader } from "./components/layout/AppHeader"
import { TaskCard } from "./components/tasks/TaskCard"
import { TaskSectionHeader } from "./components/tasks/TaskSectionHeader"
import { TodayOperationSummary } from "./components/tasks/TodayOperationSummary"
import { todayTasks } from "./data/todayTasks"
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

  useEffect(() => {
    const root = document.documentElement

    if (theme === "dark") {
      root.classList.add("dark")
    } else {
      root.classList.remove("dark")
    }

    window.localStorage.setItem("missio-theme", theme)
  }, [theme])

  const taskStats = useMemo(() => {
    return {
      totalCount: todayTasks.length,
      completedCount: todayTasks.filter((task) => task.status === "completed").length,
      waitingCount: todayTasks.filter((task) => task.status === "assigned").length,
      activeCount: todayTasks.filter((task) => task.status === "in_progress").length,
    }
  }, [])

  return (
    <main className="min-h-screen bg-[var(--missio-page-bg)] px-4 py-5 text-[var(--missio-text-main)] transition-colors duration-300">
      <section className="mx-auto flex min-h-[calc(100vh-40px)] w-full max-w-md flex-col">
        <AppHeader
          theme={theme}
          onToggleTheme={() => setTheme(theme === "light" ? "dark" : "light")}
        />

        <TodayOperationSummary
          totalCount={taskStats.totalCount}
          completedCount={taskStats.completedCount}
          activeCount={taskStats.activeCount}
          waitingCount={taskStats.waitingCount}
        />

        <TaskSectionHeader />

        <section className="flex flex-1 flex-col gap-4 pb-6">
          {todayTasks.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </section>
      </section>
    </main>
  )
}
