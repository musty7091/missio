import { CheckCircle2, CircleDot, Clock3 } from "lucide-react"

type TodayOperationSummaryProps = {
  totalCount: number
  completedCount: number
  activeCount: number
  waitingCount: number
  remainingCount: number
}

function SummaryMiniItem({
  label,
  value,
}: {
  label: string
  value: number
}) {
  return (
    <div className="min-w-0 rounded-2xl bg-white/10 px-3 py-2">
      <p className="text-lg font-black leading-none text-white">{value}</p>
      <p className="mt-1 truncate text-[0.68rem] font-bold text-slate-300">{label}</p>
    </div>
  )
}

export function TodayOperationSummary({
  totalCount,
  completedCount,
  activeCount,
  waitingCount,
  remainingCount,
}: TodayOperationSummaryProps) {
  const completionRate =
    totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0

  return (
    <section className="mb-3 rounded-[1.7rem] bg-slate-950 p-4 text-white shadow-xl shadow-slate-950/15">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-black text-cyan-200">
            <CircleDot size={13} />
            Bugünkü operasyon
          </div>

          <div className="mt-3 flex items-end gap-2">
            <p className="text-3xl font-black leading-none">{totalCount}</p>
            <p className="pb-1 text-sm font-bold text-slate-300">görev</p>
          </div>
        </div>

        <div className="shrink-0 rounded-2xl bg-cyan-300 px-3 py-2 text-center text-slate-950">
          <p className="text-lg font-black leading-none">%{completionRate}</p>
          <p className="mt-1 text-[0.62rem] font-black">tamamlandı</p>
        </div>
      </div>

      <div className="mb-3">
        <div className="mb-1.5 flex items-center justify-between text-[0.68rem] font-black text-slate-300">
          <span>Kalan görev</span>
          <span>{remainingCount}</span>
        </div>

        <div className="h-2.5 overflow-hidden rounded-full bg-white/10">
          <div
            className="h-full rounded-full bg-cyan-300 transition-all"
            style={{ width: `${completionRate}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <SummaryMiniItem label="Tamamlanan" value={completedCount} />
        <SummaryMiniItem label="Devam" value={activeCount} />
        <SummaryMiniItem label="Bekleyen" value={waitingCount} />
      </div>

      <div className="mt-3 flex items-center gap-2 text-[0.72rem] font-bold text-slate-400">
        <CheckCircle2 size={14} />
        <span>Görev detayına dokunarak işlem yapabilirsin.</span>
        <Clock3 className="ml-auto shrink-0" size={14} />
      </div>
    </section>
  )
}
