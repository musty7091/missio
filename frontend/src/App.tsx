import {
  Bell,
  Camera,
  CheckCircle2,
  Clock3,
  MapPin,
  Moon,
  PlayCircle,
  Plus,
  ShieldCheck,
  Sun,
} from "lucide-react"
import { useEffect, useState } from "react"

type ThemeMode = "light" | "dark"

const todayTasks = [
  {
    id: 1,
    title: "Reyon açılış kontrolü",
    description: "Raf düzeni, fiyat etiketleri ve eksik ürün kontrolü.",
    status: "assigned",
    priority: "high",
    time: "09:30",
    requiresPhoto: true,
    requiresLocation: true,
  },
  {
    id: 2,
    title: "Soğuk dolap sıcaklık kontrolü",
    description: "Dolap içi sıcaklık değerini kontrol edip fotoğraf ekle.",
    status: "in_progress",
    priority: "urgent",
    time: "10:15",
    requiresPhoto: true,
    requiresLocation: false,
  },
  {
    id: 3,
    title: "Günlük kasa çevresi temizliği",
    description: "Kasa önü, müşteri alanı ve ödeme noktasını kontrol et.",
    status: "completed",
    priority: "normal",
    time: "11:00",
    requiresPhoto: false,
    requiresLocation: false,
  },
]

function getStatusLabel(status: string) {
  if (status === "assigned") return "Bekliyor"
  if (status === "in_progress") return "Devam ediyor"
  if (status === "completed") return "Onay bekliyor"
  return status
}

function getActionLabel(status: string) {
  if (status === "assigned") return "Başlat"
  if (status === "in_progress") return "Tamamla"
  if (status === "completed") return "Detay"
  return "Aç"
}

function getPriorityLabel(priority: string) {
  if (priority === "urgent") return "Acil"
  if (priority === "high") return "Yüksek"
  if (priority === "normal") return "Normal"
  if (priority === "low") return "Düşük"
  return priority
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

  useEffect(() => {
    const root = document.documentElement

    if (theme === "dark") {
      root.classList.add("dark")
    } else {
      root.classList.remove("dark")
    }

    window.localStorage.setItem("missio-theme", theme)
  }, [theme])

  const completedCount = todayTasks.filter((task) => task.status === "completed").length
  const waitingCount = todayTasks.filter((task) => task.status === "assigned").length
  const activeCount = todayTasks.filter((task) => task.status === "in_progress").length

  return (
    <main className="min-h-screen bg-[var(--missio-page-bg)] px-4 py-5 text-[var(--missio-text-main)] transition-colors duration-300">
      <section className="mx-auto flex min-h-[calc(100vh-40px)] w-full max-w-md flex-col">
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
              onClick={() => setTheme(theme === "light" ? "dark" : "light")}
              className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm"
              aria-label="Tema değiştir"
            >
              {theme === "light" ? <Moon size={20} /> : <Sun size={20} />}
            </button>
          </div>
        </header>

        <section className="mb-5 overflow-hidden rounded-[2rem] bg-slate-950 p-5 text-white shadow-xl shadow-slate-900/20 dark:bg-slate-900">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm text-teal-200">Bugünkü operasyon</p>
              <h2 className="mt-2 text-3xl font-black tracking-tight">{todayTasks.length} görev</h2>
              <p className="mt-2 max-w-[260px] text-sm leading-6 text-slate-300">
                Fotoğraf kanıtı, konum kontrolü ve manager onayı tek ekranda.
              </p>
            </div>

            <div className="rounded-3xl bg-white/10 p-3">
              <ShieldCheck className="text-teal-300" size={30} />
            </div>
          </div>

          <div className="mt-5 grid grid-cols-3 gap-3">
            <div className="rounded-2xl bg-white/10 p-3">
              <p className="text-xl font-bold">{completedCount}</p>
              <p className="mt-1 text-xs text-slate-300">Tamamlanan</p>
            </div>
            <div className="rounded-2xl bg-white/10 p-3">
              <p className="text-xl font-bold">{activeCount}</p>
              <p className="mt-1 text-xs text-slate-300">Aktif</p>
            </div>
            <div className="rounded-2xl bg-white/10 p-3">
              <p className="text-xl font-bold">{waitingCount}</p>
              <p className="mt-1 text-xs text-slate-300">Bekleyen</p>
            </div>
          </div>
        </section>

        <section className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold">Bugünkü görevler</h2>
            <p className="text-sm text-[var(--missio-text-muted)]">Rutin ve ekstra görevlerin</p>
          </div>

          <button
            type="button"
            className="flex items-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 py-3 text-sm font-bold text-white shadow-lg shadow-teal-500/20"
          >
            <Plus size={18} />
            Ekle
          </button>
        </section>

        <section className="flex flex-1 flex-col gap-4 pb-6">
          {todayTasks.map((task) => (
            <article
              key={task.id}
              className="rounded-[1.75rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-sm transition-colors duration-300"
            >
              <div className="mb-3 flex items-start justify-between gap-3">
                <div>
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-[var(--missio-primary-soft)] px-3 py-1 text-xs font-bold text-teal-700 dark:text-teal-200">
                      {getStatusLabel(task.status)}
                    </span>
                    <span className="rounded-full bg-indigo-100 px-3 py-1 text-xs font-bold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-200">
                      {getPriorityLabel(task.priority)}
                    </span>
                  </div>

                  <h3 className="text-base font-bold leading-6">{task.title}</h3>
                  <p className="mt-1 text-sm leading-6 text-[var(--missio-text-muted)]">
                    {task.description}
                  </p>
                </div>

                <div className="rounded-2xl bg-slate-100 p-3 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                  {task.status === "completed" ? <CheckCircle2 size={22} /> : <Clock3 size={22} />}
                </div>
              </div>

              <div className="mb-4 flex flex-wrap gap-2">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--missio-border)] px-3 py-1.5 text-xs font-semibold text-[var(--missio-text-muted)]">
                  <Clock3 size={14} />
                  {task.time}
                </span>

                {task.requiresPhoto && (
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--missio-border)] px-3 py-1.5 text-xs font-semibold text-[var(--missio-text-muted)]">
                    <Camera size={14} />
                    Fotoğraf
                  </span>
                )}

                {task.requiresLocation && (
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--missio-border)] px-3 py-1.5 text-xs font-semibold text-[var(--missio-text-muted)]">
                    <MapPin size={14} />
                    Konum
                  </span>
                )}
              </div>

              <div className="flex gap-3">
                {task.requiresPhoto && (
                  <button
                    type="button"
                    className="flex flex-1 items-center justify-center gap-2 rounded-2xl border border-[var(--missio-border)] px-4 py-3 text-sm font-bold"
                  >
                    <Camera size={18} />
                    Fotoğraf
                  </button>
                )}

                <button
                  type="button"
                  className="flex flex-1 items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 py-3 text-sm font-bold text-white shadow-lg shadow-teal-500/20"
                >
                  <PlayCircle size={18} />
                  {getActionLabel(task.status)}
                </button>
              </div>
            </article>
          ))}
        </section>
      </section>
    </main>
  )
}
