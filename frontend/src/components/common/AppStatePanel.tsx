import { Loader2, RefreshCw } from "lucide-react"
import type { ReactNode } from "react"

type AppStatePanelTone = "neutral" | "error" | "success" | "warning"

type AppStatePanelProps = {
  icon: ReactNode
  eyebrow?: string
  title: string
  description: string
  tone?: AppStatePanelTone
  actionLabel?: string
  onAction?: () => void
}

type FullScreenStatusProps = {
  title: string
  description: string
}

const toneClasses: Record<AppStatePanelTone, string> = {
  neutral: "bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200",
  error: "bg-red-50 text-red-600 dark:bg-red-950 dark:text-red-200",
  success: "bg-emerald-50 text-emerald-600 dark:bg-emerald-950 dark:text-emerald-200",
  warning: "bg-amber-50 text-amber-600 dark:bg-amber-950 dark:text-amber-200",
}

export function FullScreenStatus({ title, description }: FullScreenStatusProps) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--missio-page-bg)] px-4 text-[var(--missio-text-main)]">
      <section className="w-full max-w-sm rounded-[2rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-6 text-center shadow-2xl shadow-slate-900/10">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-[1.5rem] bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
          <Loader2 className="animate-spin" size={30} />
        </div>

        <h1 className="mt-5 text-2xl font-black tracking-tight">{title}</h1>

        <p className="mt-2 text-sm font-semibold leading-6 text-[var(--missio-text-muted)]">
          {description}
        </p>
      </section>
    </main>
  )
}

export function AppStatePanel({
  icon,
  eyebrow,
  title,
  description,
  tone = "neutral",
  actionLabel,
  onAction,
}: AppStatePanelProps) {
  return (
    <section className="rounded-[2rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-6 text-center shadow-xl shadow-slate-900/5">
      <div className={`mx-auto flex h-16 w-16 items-center justify-center rounded-[1.5rem] ${toneClasses[tone]}`}>
        {icon}
      </div>

      {eyebrow && (
        <p className="mt-5 text-xs font-black uppercase tracking-[0.18em] text-cyan-500">
          {eyebrow}
        </p>
      )}

      <h2 className="mt-2 text-2xl font-black tracking-tight">{title}</h2>

      <p className="mt-3 text-sm font-semibold leading-6 text-[var(--missio-text-muted)]">
        {description}
      </p>

      {actionLabel && onAction && (
        <button
          type="button"
          onClick={onAction}
          className="mt-5 inline-flex items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-5 py-3 text-sm font-black text-white shadow-lg shadow-teal-500/20 transition active:scale-95"
        >
          <RefreshCw size={17} />
          {actionLabel}
        </button>
      )}
    </section>
  )
}

export function TaskLoadingSkeleton() {
  return (
    <section className="rounded-[1.75rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
          <Loader2 className="animate-spin" size={22} />
        </div>

        <div>
          <p className="text-sm font-black">Görevler yükleniyor</p>
          <p className="mt-1 text-xs font-semibold text-[var(--missio-text-muted)]">
            Bugünkü operasyon bilgileri hazırlanıyor.
          </p>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        <div className="h-4 w-3/4 animate-pulse rounded-full bg-slate-200 dark:bg-slate-800" />
        <div className="h-4 w-1/2 animate-pulse rounded-full bg-slate-200 dark:bg-slate-800" />
        <div className="h-12 w-full animate-pulse rounded-2xl bg-slate-200 dark:bg-slate-800" />
      </div>
    </section>
  )
}
