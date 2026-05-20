import { Plus } from "lucide-react"

export function TaskSectionHeader() {
  return (
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
  )
}
