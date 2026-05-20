import { BarChart3, Bell, ClipboardCheck, UserRound } from "lucide-react"

const navigationItems = [
  {
    label: "Görevler",
    icon: ClipboardCheck,
    isActive: true,
  },
  {
    label: "Bildirim",
    icon: Bell,
    isActive: false,
  },
  {
    label: "Rapor",
    icon: BarChart3,
    isActive: false,
  },
  {
    label: "Profil",
    icon: UserRound,
    isActive: false,
  },
]

export function BottomNavigation() {
  return (
    <nav className="sticky bottom-4 z-20 mt-auto rounded-[2rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)]/95 p-2 shadow-2xl shadow-slate-900/10 backdrop-blur-xl dark:shadow-black/30">
      <div className="grid grid-cols-4 gap-1">
        {navigationItems.map((item) => {
          const Icon = item.icon

          return (
            <button
              key={item.label}
              type="button"
              className={
                item.isActive
                  ? "flex flex-col items-center justify-center gap-1 rounded-3xl bg-[var(--missio-primary)] px-2 py-3 text-xs font-bold text-white shadow-lg shadow-teal-500/20"
                  : "flex flex-col items-center justify-center gap-1 rounded-3xl px-2 py-3 text-xs font-bold text-[var(--missio-text-muted)]"
              }
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
