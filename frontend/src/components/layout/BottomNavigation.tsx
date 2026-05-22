import { BarChart3, Bell, ClipboardCheck, UserRound } from "lucide-react"

export type AppTab = "tasks" | "notifications" | "reports" | "profile"

type NavigationItem = {
  id: AppTab
  label: string
  shortLabel: string
  icon: typeof ClipboardCheck
}

type BottomNavigationProps = {
  activeTab: AppTab
  notificationCount: number
  onTabChange: (tab: AppTab) => void
}

const navigationItems: NavigationItem[] = [
  {
    id: "tasks",
    label: "Görevler",
    shortLabel: "Görev",
    icon: ClipboardCheck,
  },
  {
    id: "notifications",
    label: "Bildirimler",
    shortLabel: "Bildirim",
    icon: Bell,
  },
  {
    id: "reports",
    label: "Raporlar",
    shortLabel: "Rapor",
    icon: BarChart3,
  },
  {
    id: "profile",
    label: "Profil",
    shortLabel: "Profil",
    icon: UserRound,
  },
]

export function BottomNavigation({
  activeTab,
  notificationCount,
  onTabChange,
}: BottomNavigationProps) {
  const notificationLabel = notificationCount > 9 ? "9+" : String(notificationCount)

  return (
    <nav
      className="sticky bottom-3 z-20 mt-auto rounded-[2rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)]/95 p-2 shadow-2xl shadow-slate-900/10 backdrop-blur-xl dark:shadow-black/30"
      aria-label="Alt navigasyon"
    >
      <div className="grid grid-cols-4 gap-1">
        {navigationItems.map((item) => {
          const Icon = item.icon
          const isActive = item.id === activeTab
          const shouldShowBadge = item.id === "notifications" && notificationCount > 0

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onTabChange(item.id)}
              aria-current={isActive ? "page" : undefined}
              className={
                isActive
                  ? "relative flex min-h-[4.15rem] flex-col items-center justify-center gap-1 rounded-3xl bg-[var(--missio-primary)] px-2 py-3 text-xs font-black text-white shadow-lg shadow-teal-500/20 transition active:scale-95"
                  : "relative flex min-h-[4.15rem] flex-col items-center justify-center gap-1 rounded-3xl px-2 py-3 text-xs font-black text-[var(--missio-text-muted)] transition active:scale-95"
              }
            >
              <span className="relative">
                <Icon size={20} />

                {shouldShowBadge && (
                  <span className="absolute -right-3 -top-3 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[0.62rem] font-black text-white ring-2 ring-[var(--missio-card-bg)]">
                    {notificationLabel}
                  </span>
                )}
              </span>

              <span className="leading-none">{item.shortLabel}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
