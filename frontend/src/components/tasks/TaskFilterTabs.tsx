import { useTranslation } from "../../i18n/language"
import type { TodayTask } from "../../types/task"

export type TaskListFilter = "all" | "waiting" | "active" | "completed"

type TaskFilterTabsProps = {
  activeFilter: TaskListFilter
  tasks: TodayTask[]
  onFilterChange: (filter: TaskListFilter) => void
}

type FilterItem = {
  key: TaskListFilter
  label: string
  count: number
}

export function TaskFilterTabs({
  activeFilter,
  tasks,
  onFilterChange,
}: TaskFilterTabsProps) {
  const { t } = useTranslation()

  const waitingCount = tasks.filter(
    (task) => task.status === "assigned" || task.status === "rejected",
  ).length

  const completedCount = tasks.filter(
    (task) => task.status === "completed" || task.status === "approved",
  ).length

  const filterItems: FilterItem[] = [
    {
      key: "all",
      label: t("task.filter.all"),
      count: tasks.length,
    },
    {
      key: "waiting",
      label: t("task.filter.waiting"),
      count: waitingCount,
    },
    {
      key: "active",
      label: t("task.filter.active"),
      count: tasks.filter((task) => task.status === "in_progress").length,
    },
    {
      key: "completed",
      label: t("task.filter.completed"),
      count: completedCount,
    },
  ]

  return (
    <div className="mb-3 grid grid-cols-4 gap-2">
      {filterItems.map((item) => {
        const isActive = activeFilter === item.key

        return (
          <button
            key={item.key}
            type="button"
            onClick={() => onFilterChange(item.key)}
            className={
              isActive
                ? "min-w-0 rounded-2xl bg-[var(--missio-primary)] px-1.5 py-2.5 text-center text-white shadow-lg shadow-teal-500/20"
                : "min-w-0 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-1.5 py-2.5 text-center text-[var(--missio-text-muted)]"
            }
          >
            <span className="block truncate text-[0.72rem] font-black leading-none">
              {item.label}
            </span>

            <span
              className={
                isActive
                  ? "mt-1.5 inline-flex min-w-6 justify-center rounded-full bg-white/20 px-1.5 py-0.5 text-[0.62rem] font-black text-white"
                  : "mt-1.5 inline-flex min-w-6 justify-center rounded-full bg-[var(--missio-page-bg)] px-1.5 py-0.5 text-[0.62rem] font-black text-[var(--missio-text-muted)]"
              }
            >
              {item.count}
            </span>
          </button>
        )
      })}
    </div>
  )
}
