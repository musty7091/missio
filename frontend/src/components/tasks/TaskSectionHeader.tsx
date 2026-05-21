type TaskSectionHeaderProps = {
  totalCount: number
  routineCount: number
  extraCount: number
}

export function TaskSectionHeader({
  totalCount,
  routineCount,
  extraCount,
}: TaskSectionHeaderProps) {
  return (
    <section className="mb-4 rounded-[1.75rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-sm">
      <p className="text-xs font-black uppercase tracking-[0.16em] text-cyan-500">
        Günlük görev listesi
      </p>

      <div className="mt-1 flex items-end justify-between gap-3">
        <div>
          <h2 className="text-xl font-black tracking-tight">Bugünkü görevler</h2>
          <p className="mt-1 text-sm font-semibold text-[var(--missio-text-muted)]">
            Göreve dokun, detayları görüntüle.
          </p>
        </div>

        <div className="shrink-0 rounded-2xl bg-[var(--missio-primary-soft)] px-3 py-2 text-right">
          <p className="text-lg font-black text-cyan-700 dark:text-cyan-200">{totalCount}</p>
          <p className="text-[0.65rem] font-black text-cyan-700/70 dark:text-cyan-200/70">
            toplam
          </p>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <span className="rounded-full border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-3 py-1.5 text-xs font-black text-[var(--missio-text-muted)]">
          {routineCount} rutin
        </span>

        <span className="rounded-full border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-3 py-1.5 text-xs font-black text-[var(--missio-text-muted)]">
          {extraCount} ekstra
        </span>
      </div>
    </section>
  )
}
