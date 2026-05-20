import { Bell, Moon, Sun } from "lucide-react"
import type { ThemeMode } from "../../types/task"

type AppHeaderProps = {
  theme: ThemeMode
  onToggleTheme: () => void
}

export function AppHeader({ theme, onToggleTheme }: AppHeaderProps) {
  return (
    <header className="mb-5 flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-[var(--missio-text-muted)]">Missio</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight">Günaydın Ahmet 👋</h1>
      </div>

      <div className="flex items-center gap-2">
        <button
          type="button"
          className="relative rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm"
          aria-label="Bildirimler"
        >
          <Bell size={20} />
          <span className="absolute right-2 top-2 h-2.5 w-2.5 rounded-full bg-[var(--missio-danger)] ring-2 ring-[var(--missio-card-bg)]" />
        </button>

        <button
          type="button"
          onClick={onToggleTheme}
          className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm"
          aria-label="Tema değiştir"
        >
          {theme === "light" ? <Moon size={20} /> : <Sun size={20} />}
        </button>
      </div>
    </header>
  )
}
