import { ShieldCheck, TrendingUp } from "lucide-react"

type TodayOperationSummaryProps = {
  totalCount: number
  completedCount: number
  activeCount: number
  waitingCount: number
  remainingCount: number
}

export function TodayOperationSummary({
  totalCount,
  completedCount,
  activeCount,
  waitingCount,
  remainingCount,
}: TodayOperationSummaryProps) {
  const completionRate = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0

  return (
    <section className="mb-5 overflow-hidden rounded-[2rem] bg-slate-950 p-5 text-white shadow-xl shadow-slate-900/20 dark:bg-slate-900">
      <div className="relative">
        <div className="absolute -right-12 -top-12 h-36 w-36 rounded-full border border-cyan-300/20" />
        <div className="absolute right-5 top-8 h-3 w-3 rounded-full bg-cyan-300 shadow-lg shadow-cyan-300/50" />

        <div className="relative flex items-start justify-between gap-4">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-black text-cyan-200">
              <ShieldCheck size={14} />
              Bugünkü operasyon
            </div>

            <h2 className="text-3xl font-black tracking-tight">{totalCount} görev</h2>

            <p className="mt-2 max-w-[260px] text-sm font-semibold leading-6 text-slate-300">
              {remainingCount > 0
                ? `${remainingCount} görev henüz kapanmadı.`
                : "Bugünkü görevlerin tamamı kapandı."}
            </p>
          </div>

          <div className="rounded-3xl bg-white/10 p-3">
            <TrendingUp className="text-cyan-300" size={30} />
          </div>
        </div>

        <div className="relative mt-5">
          <div className="mb-2 flex items-center justify-between text-xs font-black text-slate-300">
            <span>Tamamlanma</span>
            <span>%{completionRate}</span>
          </div>

          <div className="h-3 overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full rounded-full bg-cyan-300 transition-all duration-500"
              style={{ width: `${completionRate}%` }}
            />
          </div>
        </div>

        <div className="relative mt-5 grid grid-cols-3 gap-3">
          <div className="rounded-2xl bg-white/10 p-3">
            <p className="text-xl font-black">{completedCount}</p>
            <p className="mt-1 text-xs font-semibold text-slate-300">Tamamlanan</p>
          </div>

          <div className="rounded-2xl bg-white/10 p-3">
            <p className="text-xl font-black">{activeCount}</p>
            <p className="mt-1 text-xs font-semibold text-slate-300">Devam eden</p>
          </div>

          <div className="rounded-2xl bg-white/10 p-3">
            <p className="text-xl font-black">{waitingCount}</p>
            <p className="mt-1 text-xs font-semibold text-slate-300">Bekleyen</p>
          </div>
        </div>
      </div>
    </section>
  )
}
