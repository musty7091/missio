import {
  BarChart3,
  Bell,
  Building2,
  ClipboardCheck,
  FileCheck2,
  Home,
  ShieldCheck,
  UserRound,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"

export type AppTab = "tasks" | "notifications" | "reports" | "profile"

type NavigationItem = {
  id: AppTab
  label: string
  icon: typeof ClipboardCheck
}

type BottomNavigationProps = {
  activeTab: AppTab
  notificationCount: number
  role: string
  onTabChange: (tab: AppTab) => void
}

const NOTIFICATION_SEEN_DATE_STORAGE_KEY = "missio-notifications-seen-date"

function getLocalTodayDateKey() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, "0")
  const day = String(now.getDate()).padStart(2, "0")

  return `${year}-${month}-${day}`
}

function isSuperAdminRole(role: string) {
  return role === "super_admin"
}

function isStaffRole(role: string) {
  return role === "staff"
}

function isBossRole(role: string) {
  return role === "boss"
}

function isNotificationsSeenToday() {
  return (
    window.localStorage.getItem(NOTIFICATION_SEEN_DATE_STORAGE_KEY) ===
    getLocalTodayDateKey()
  )
}

function markNotificationsSeenToday() {
  window.localStorage.setItem(
    NOTIFICATION_SEEN_DATE_STORAGE_KEY,
    getLocalTodayDateKey(),
  )
}

function getNavigationItems(role: string): NavigationItem[] {
  if (isSuperAdminRole(role)) {
    return [
      {
        id: "tasks",
        label: "İşletme",
        icon: Building2,
      },
      {
        id: "reports",
        label: "Rapor",
        icon: BarChart3,
      },
      {
        id: "notifications",
        label: "Sistem",
        icon: ShieldCheck,
      },
      {
        id: "profile",
        label: "Profil",
        icon: UserRound,
      },
    ]
  }

  if (isStaffRole(role)) {
    return [
      {
        id: "tasks",
        label: "Görev",
        icon: ClipboardCheck,
      },
      {
        id: "notifications",
        label: "Bildirim",
        icon: Bell,
      },
      {
        id: "reports",
        label: "Kontrol",
        icon: ShieldCheck,
      },
      {
        id: "profile",
        label: "Profil",
        icon: UserRound,
      },
    ]
  }

  if (isBossRole(role)) {
    return [
      {
        id: "tasks",
        label: "Özet",
        icon: Home,
      },
      {
        id: "reports",
        label: "Rapor",
        icon: BarChart3,
      },
      {
        id: "notifications",
        label: "Onay",
        icon: FileCheck2,
      },
      {
        id: "profile",
        label: "Profil",
        icon: UserRound,
      },
    ]
  }

  return [
    {
      id: "tasks",
      label: "Operasyon",
      icon: ClipboardCheck,
    },
    {
      id: "notifications",
      label: "Onay",
      icon: FileCheck2,
    },
    {
      id: "reports",
      label: "Gün Kapat",
      icon: ShieldCheck,
    },
    {
      id: "profile",
      label: "Profil",
      icon: UserRound,
    },
  ]
}

export function BottomNavigation({
  activeTab,
  notificationCount,
  role,
  onTabChange,
}: BottomNavigationProps) {
  const [hasSeenNotificationsToday, setHasSeenNotificationsToday] = useState(() =>
    isNotificationsSeenToday(),
  )

  useEffect(() => {
    if (activeTab === "notifications") {
      markNotificationsSeenToday()
      setHasSeenNotificationsToday(true)
    }
  }, [activeTab])

  function handleTabChange(tab: AppTab) {
    if (tab === "notifications") {
      markNotificationsSeenToday()
      setHasSeenNotificationsToday(true)
    }

    onTabChange(tab)
  }

  const navigationItems = useMemo(() => getNavigationItems(role), [role])
  const visibleNotificationCount = hasSeenNotificationsToday ? 0 : notificationCount
  const notificationLabel =
    visibleNotificationCount > 9 ? "9+" : String(visibleNotificationCount)
  const shouldUseBadge = isStaffRole(role)

  return (
    <nav
      className="sticky bottom-3 z-20 mt-auto rounded-[2rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)]/95 p-2 shadow-2xl shadow-slate-900/10 backdrop-blur-xl dark:shadow-black/30"
      aria-label="Alt navigasyon"
    >
      <div className="grid grid-cols-4 gap-1">
        {navigationItems.map((item) => {
          const Icon = item.icon
          const isActive = item.id === activeTab
          const shouldShowBadge =
            shouldUseBadge &&
            item.id === "notifications" &&
            visibleNotificationCount > 0

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => handleTabChange(item.id)}
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

              <span className="leading-none">{item.label}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}