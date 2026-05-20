import { ShieldCheck } from "lucide-react"

type TodayOperationSummaryProps = {
  totalCount: number
  completedCount: number
  activeCount: number
  waitingCount: number
}

export function TodayOperationSummary({
  totalCount,
  completedCount,
  activeCount,
  waitingCount,
}: TodayOperationSummaryProps) {
  return (
    <section className="mb-5 overflow-hidden rounded-[2rem] bg-slate-950 p-5 text-white shadow-xl shadow-slate-900/20 dark:bg-slate-900">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-teal-200">Bugünkü operasyon</p>
          <h2 className="mt-2 text-3xl font-black tracking-tight">{totalCount} görev</h2>
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
  )
}
