import { CalendarCheck2, Sparkles } from "lucide-react"
import { useTranslation } from "../../i18n/language"

type TaskGroupHeaderProps = {
  type: "routine" | "extra"
  count: number
}

export function TaskGroupHeader({ type, count }: TaskGroupHeaderProps) {
  const { t } = useTranslation()
  const isRoutine = type === "routine"

  const title = isRoutine
    ? t("task.type.routineGroupTitle")
    : t("task.type.oneTimeGroupTitle")

  const description = isRoutine
    ? t("task.type.routineGroupDescription")
    : t("task.type.oneTimeGroupDescription")

  const Icon = isRoutine ? CalendarCheck2 : Sparkles

  return (
    <div
      className={
        isRoutine
          ? "mt-2 overflow-hidden rounded-2xl border border-cyan-200 bg-cyan-50/80 shadow-sm dark:border-cyan-900 dark:bg-cyan-950/30"
          : "mt-2 overflow-hidden rounded-2xl border border-amber-200 bg-amber-50/90 shadow-sm dark:border-amber-900 dark:bg-amber-950/30"
      }
    >
      <div className="flex">
        <div className={isRoutine ? "w-1.5 shrink-0 bg-cyan-400" : "w-1.5 shrink-0 bg-amber-400"} />

        <div className="flex min-w-0 flex-1 items-center justify-between gap-3 px-3 py-2.5">
          <div className="flex min-w-0 items-center gap-2.5">
            <div
              className={
                isRoutine
                  ? "flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl bg-cyan-500 text-white shadow-lg shadow-cyan-500/20"
                  : "flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl bg-amber-400 text-slate-950 shadow-lg shadow-amber-500/20"
              }
            >
              <Icon size={18} />
            </div>

            <div className="min-w-0">
              <p
                className={
                  isRoutine
                    ? "truncate text-sm font-black text-cyan-950 dark:text-cyan-100"
                    : "truncate text-sm font-black text-amber-950 dark:text-amber-100"
                }
              >
                {title}
              </p>

              <p
                className={
                  isRoutine
                    ? "truncate text-[0.68rem] font-bold text-cyan-700 dark:text-cyan-300"
                    : "truncate text-[0.68rem] font-bold text-amber-700 dark:text-amber-300"
                }
              >
                {description}
              </p>
            </div>
          </div>

          <span
            className={
              isRoutine
                ? "shrink-0 rounded-full bg-cyan-500 px-2.5 py-1 text-xs font-black text-white"
                : "shrink-0 rounded-full bg-amber-400 px-2.5 py-1 text-xs font-black text-slate-950"
            }
          >
            {count}
          </span>
        </div>
      </div>
    </div>
  )
}
