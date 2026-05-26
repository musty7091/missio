import { useState } from "react"
import { Plus } from "lucide-react"
import { useTranslation } from "../../i18n/language"

import { TaskAssignSheet } from "../tasks/TaskAssignSheet"

type BossTaskAssignCardProps = {
  businessId: number | null
  onChanged: () => void
}

export function BossTaskAssignCard({
  businessId,
  onChanged,
}: BossTaskAssignCardProps) {
  const { t } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  async function handleCreated() {
    onChanged()
  }

  return (
    <section className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
            {t("boss.summary.assign.eyebrow")}
          </p>

          <h2 className="mt-1 text-base font-black text-[var(--missio-text-main)]">
            {t("boss.summary.assign.title")}
          </h2>

          <p className="mt-1 text-xs font-bold leading-5 text-[var(--missio-text-muted)]">
            {t("boss.summary.assign.description")}
          </p>
        </div>

        <button
          type="button"
          onClick={() => {
            setSuccessMessage(null)
            setIsOpen(true)
          }}
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary)] text-white shadow-lg shadow-teal-500/20 transition active:scale-95"
          aria-label={t("boss.summary.assign.title")}
        >
          <Plus size={22} />
        </button>
      </div>

      {successMessage && (
        <div className="mt-3 rounded-2xl bg-emerald-50 p-3 text-sm font-black text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-200">
          {successMessage}
        </div>
      )}

      <TaskAssignSheet
        businessId={businessId}
        isOpen={isOpen}
        assignableRoles={["staff", "manager"]}
        defaultRequiresManagerApproval={false}
        allowLocationRequirement
        onClose={() => setIsOpen(false)}
        onCreated={handleCreated}
        onSuccess={setSuccessMessage}
      />
    </section>
  )
}
