import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  CreditCard,
  Info,
  Loader2,
  PauseCircle,
  PlayCircle,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  TrendingDown,
  TrendingUp,
} from "lucide-react"
import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react"

import {
  changeBusinessPlan,
  extendBusinessSubscription,
  getBusinessSubscriptionOverview,
  updateBusinessSubscriptionStatus,
} from "../../services/businessService"
import { ApiError } from "../../services/httpClient"
import type {
  BusinessResponse,
  BusinessSubscriptionOverviewResponse,
  BusinessSubscriptionResponse,
  ChangeBusinessPlanRequest,
  ExtendBusinessSubscriptionRequest,
  SubscriptionPlanResponse,
  UpdateBusinessSubscriptionStatusRequest,
} from "../../types/business"

type ActionMode = "extend" | "change-plan" | "status"
type BillingPeriod = ExtendBusinessSubscriptionRequest["billing_period"]
type SubscriptionStatus = UpdateBusinessSubscriptionStatusRequest["status"]

type ExtendFormState = {
  billingPeriod: BillingPeriod
  durationDays: string
  notes: string
}

type ChangePlanFormState = {
  planCode: string
  preserveRemainingTime: boolean
  notes: string
}

type StatusFormState = {
  notes: string
}

const initialExtendFormState: ExtendFormState = {
  billingPeriod: "monthly",
  durationDays: "30",
  notes: "",
}

const initialChangePlanFormState: ChangePlanFormState = {
  planCode: "",
  preserveRemainingTime: true,
  notes: "",
}

const initialStatusFormState: StatusFormState = {
  notes: "",
}

const durationByBillingPeriod: Partial<Record<BillingPeriod, string>> = {
  trial: "14",
  monthly: "30",
  yearly: "365",
}

function optionalText(value: string) {
  const trimmedValue = value.trim()

  if (!trimmedValue) {
    return null
  }

  return trimmedValue
}

function getErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    const data = error.data as { detail?: unknown; message?: unknown } | null

    if (typeof data?.detail === "string") {
      return data.detail
    }

    if (typeof data?.detail === "object" && data.detail !== null) {
      const nestedDetail = data.detail as { message?: unknown; errors?: unknown }

      if (typeof nestedDetail.message === "string") {
        if (Array.isArray(nestedDetail.errors) && nestedDetail.errors.length > 0) {
          return `${nestedDetail.message} ${nestedDetail.errors.join(" ")}`
        }

        return nestedDetail.message
      }
    }

    if (typeof data?.message === "string") {
      return data.message
    }

    return error.message
  }

  if (error instanceof Error) {
    return error.message
  }

  return "İşlem tamamlanamadı."
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "Süresiz"
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return "Tarih yok"
  }

  return date.toLocaleString("tr-TR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function formatMoney(value: string | null, currency: string) {
  if (!value) {
    return "-"
  }

  const numericValue = Number(value)

  if (Number.isNaN(numericValue)) {
    return `${value} ${currency}`
  }

  return `${numericValue.toLocaleString("tr-TR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${currency}`
}

function getStatusLabel(status: string | null | undefined) {
  const labels: Record<string, string> = {
    trialing: "Deneme sürecinde",
    active: "Aktif müşteri",
    suspended: "Askıda",
    cancelled: "İptal edilmiş",
    expired: "Süresi doldu",
  }

  if (!status) {
    return "Abonelik yok"
  }

  return labels[status] ?? status
}

function getAccessLabel(status: string | null | undefined, isExpired: boolean) {
  if (isExpired) {
    return "Süresi doldu"
  }

  if (status === "suspended") {
    return "Giriş kapalı"
  }

  if (status === "cancelled") {
    return "İptal edilmiş"
  }

  if (status === "trialing" || status === "active") {
    return "Giriş açık"
  }

  return "Kontrol gerekli"
}

function getAccessHelper(status: string | null | undefined, isExpired: boolean) {
  if (isExpired) {
    return "Süre uzatılmadan müşteri giriş yapamaz."
  }

  if (status === "suspended") {
    return "Müşteri kullanıcıları sisteme giriş yapamaz."
  }

  if (status === "cancelled") {
    return "Müşteri erişimi kapalıdır."
  }

  return "Müşteri kullanımı açık."
}

function getExtendActionLabel(status: string | null | undefined) {
  if (status === "trialing") {
    return "Denemeyi uzat"
  }

  return "Aboneliği yenile"
}

function getChangePlanActionLabel(status: string | null | undefined) {
  if (status === "trialing") {
    return "Ücretli plana geçir"
  }

  return "Paketi değiştir"
}

function getStatusActionLabel(status: string | null | undefined) {
  if (status === "suspended") {
    return "Tekrar aktif et"
  }

  return "İşletmeyi askıya al"
}


function addDays(date: Date, days: number) {
  const copiedDate = new Date(date)
  copiedDate.setDate(copiedDate.getDate() + days)
  return copiedDate
}

function getEstimatedExtendedEndDate(
  currentSubscription: BusinessSubscriptionResponse | null,
  durationDays: number,
) {
  const now = new Date()
  const currentEndDate = currentSubscription?.ends_at_utc
    ? new Date(currentSubscription.ends_at_utc)
    : null

  if (
    currentEndDate !== null &&
    !Number.isNaN(currentEndDate.getTime()) &&
    currentEndDate > now
  ) {
    return addDays(currentEndDate, durationDays)
  }

  return addDays(now, durationDays)
}

function getPlanDirection(
  currentPlan: SubscriptionPlanResponse | null,
  selectedPlan: SubscriptionPlanResponse | null,
) {
  if (!currentPlan || !selectedPlan) {
    return {
      label: "Paket seçimi",
      icon: <CreditCard size={18} />,
      helper: "Mevcut paket ve hedef paket karşılaştırılamıyor.",
      tone: "neutral" as const,
    }
  }

  if (selectedPlan.id === currentPlan.id) {
    return {
      label: "Aynı plan",
      icon: <Info size={18} />,
      helper: "Seçilen paket mevcut paket ile aynı.",
      tone: "neutral" as const,
    }
  }

  if (selectedPlan.max_users > currentPlan.max_users) {
    return {
      label: "Paket yükseltme",
      icon: <TrendingUp size={18} />,
      helper: "Yeni paket hemen aktif olur, limitler hemen yükselir.",
      tone: "success" as const,
    }
  }

  return {
    label: "Paket düşürme",
    icon: <TrendingDown size={18} />,
    helper: "Aktif kullanıcı sayısı yeni paket limitini aşıyorsa işlem engellenir.",
    tone: "warning" as const,
  }
}

function InfoCard({
  label,
  value,
  helper,
}: {
  label: string
  value: string | number
  helper?: string
}) {
  return (
    <div className="rounded-[1.25rem] border border-[var(--missio-border)] bg-[var(--missio-soft-bg)] p-3">
      <p className="text-[0.65rem] font-black uppercase tracking-[0.14em] text-[var(--missio-text-muted)]">
        {label}
      </p>
      <p className="mt-1 text-base font-black text-[var(--missio-text-main)]">
        {value}
      </p>
      {helper && (
        <p className="mt-1 text-xs font-bold leading-5 text-[var(--missio-text-muted)]">
          {helper}
        </p>
      )}
    </div>
  )
}

function ActionButton({
  mode,
  activeMode,
  label,
  helper,
  icon,
  onClick,
}: {
  mode: ActionMode
  activeMode: ActionMode
  label: string
  helper: string
  icon: ReactNode
  onClick: (mode: ActionMode) => void
}) {
  const isActive = mode === activeMode

  return (
    <button
      type="button"
      onClick={() => onClick(mode)}
      aria-pressed={isActive}
      className={
        isActive
          ? "rounded-[1.35rem] bg-[var(--missio-primary)] p-3 text-left text-white shadow-lg shadow-teal-500/20 ring-2 ring-cyan-200 transition active:scale-95 dark:ring-cyan-900"
          : "rounded-[1.35rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 text-left text-[var(--missio-text-main)] shadow-sm transition active:scale-95"
      }
    >
      <div className="mb-2 flex items-center gap-2">
        {icon}
        <p className="text-sm font-black">{label}</p>
      </div>
      <p className="text-xs font-bold leading-5 opacity-80">{helper}</p>
    </button>
  )
}

function MessageBox({
  type,
  children,
}: {
  type: "success" | "error" | "info" | "warning"
  children: ReactNode
}) {
  const className =
    type === "success"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200"
      : type === "error"
        ? "border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-200"
        : type === "warning"
          ? "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200"
          : "border-cyan-200 bg-cyan-50 text-cyan-800 dark:border-cyan-900 dark:bg-cyan-950/30 dark:text-cyan-200"

  return (
    <div className={`rounded-[1.25rem] border p-3 text-sm font-bold leading-6 ${className}`}>
      {children}
    </div>
  )
}

export function SuperAdminPlanPanel({
  business,
  onChanged,
}: {
  business: BusinessResponse
  onChanged?: () => void
}) {
  const [overview, setOverview] = useState<BusinessSubscriptionOverviewResponse | null>(null)
  const [activeMode, setActiveMode] = useState<ActionMode>("extend")
  const [extendForm, setExtendForm] = useState<ExtendFormState>(initialExtendFormState)
  const [changePlanForm, setChangePlanForm] = useState<ChangePlanFormState>(
    initialChangePlanFormState,
  )
  const [statusForm, setStatusForm] = useState<StatusFormState>(initialStatusFormState)
  const [isLoading, setIsLoading] = useState(false)
  const [savingMode, setSavingMode] = useState<ActionMode | null>(null)
  const [loadErrorMessage, setLoadErrorMessage] = useState<string | null>(null)
  const [operationErrorMessage, setOperationErrorMessage] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  useEffect(() => {
    void loadOverview(true)
  }, [business.id])

  const currentSubscription = overview?.current_subscription ?? null
  const currentPlan = overview?.current_plan ?? null
  const availablePlans = overview?.available_plans ?? []
  const isTrialCustomer = currentSubscription?.status === "trialing"

  const planOptions = useMemo(() => {
    if (isTrialCustomer) {
      const paidPlans = availablePlans.filter((plan) => plan.code !== "trial")

      return paidPlans.length > 0 ? paidPlans : availablePlans
    }

    return availablePlans
  }, [availablePlans, isTrialCustomer])

  const selectedPlan = useMemo(() => {
    return (
      availablePlans.find((plan) => plan.code === changePlanForm.planCode) ??
      null
    )
  }, [availablePlans, changePlanForm.planCode])

  const durationDays = useMemo(() => {
    const value = Number(extendForm.durationDays)

    if (!Number.isFinite(value) || value < 1) {
      return 0
    }

    return value
  }, [extendForm.durationDays])

  const estimatedExtendedEndDate = useMemo(() => {
    if (durationDays < 1) {
      return null
    }

    return getEstimatedExtendedEndDate(currentSubscription, durationDays)
  }, [currentSubscription, durationDays])

  const planDirection = getPlanDirection(currentPlan, selectedPlan)
  const isSamePlan = Boolean(currentPlan && selectedPlan && currentPlan.id === selectedPlan.id)
  const isDowngradeBlocked = Boolean(
    overview &&
      selectedPlan &&
      overview.active_user_count > selectedPlan.max_users,
  )

  async function loadOverview(resetForms: boolean) {
    setIsLoading(true)
    setLoadErrorMessage(null)

    try {
      const response = await getBusinessSubscriptionOverview(business.id)
      setOverview(response)

      if (resetForms) {
        const firstPaidPlanCode =
          response.available_plans.find((plan) => plan.code !== "trial")?.code ??
          response.available_plans[0]?.code ??
          ""
        const currentPlanCode =
          response.current_plan?.code === "trial"
            ? firstPaidPlanCode
            : response.current_plan?.code ?? firstPaidPlanCode

        setChangePlanForm({
          ...initialChangePlanFormState,
          planCode: currentPlanCode,
        })
        setExtendForm(initialExtendFormState)
        setStatusForm(initialStatusFormState)
        setSuccessMessage(null)
        setOperationErrorMessage(null)
      }
    } catch (error) {
      setLoadErrorMessage(getErrorMessage(error))
    } finally {
      setIsLoading(false)
    }
  }

  function handleBillingPeriodChange(value: BillingPeriod) {
    setExtendForm((currentForm) => ({
      ...currentForm,
      billingPeriod: value,
      durationDays: durationByBillingPeriod[value] ?? currentForm.durationDays,
    }))
  }

  async function refreshAfterOperation(message: string) {
    setSuccessMessage(message)
    setOperationErrorMessage(null)
    await loadOverview(false)
    onChanged?.()
  }

  async function handleExtendSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (durationDays < 1 || durationDays > 3650) {
      setOperationErrorMessage("Süre 1 ile 3650 gün arasında olmalıdır.")
      return
    }

    setSavingMode("extend")
    setOperationErrorMessage(null)
    setSuccessMessage(null)

    try {
      const response = await extendBusinessSubscription(business.id, {
        duration_days: durationDays,
        billing_period: extendForm.billingPeriod,
        notes: optionalText(extendForm.notes),
      })

      await refreshAfterOperation(response.message)
      setExtendForm(initialExtendFormState)
    } catch (error) {
      setOperationErrorMessage(getErrorMessage(error))
    } finally {
      setSavingMode(null)
    }
  }

  async function handleChangePlanSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!changePlanForm.planCode) {
      setOperationErrorMessage("Lütfen hedef plan seç.")
      return
    }

    if (isSamePlan) {
      setOperationErrorMessage("Seçilen paket mevcut paket ile aynı. Plan değişikliği yapılmadı.")
      return
    }

    if (isDowngradeBlocked) {
      setOperationErrorMessage(
        "Bu düşürme işlemi yapılamaz. Aktif kullanıcı sayısı seçilen paket limitini aşıyor.",
      )
      return
    }

    setSavingMode("change-plan")
    setOperationErrorMessage(null)
    setSuccessMessage(null)

    try {
      const payload: ChangeBusinessPlanRequest = {
        plan_code: changePlanForm.planCode,
        preserve_remaining_time: changePlanForm.preserveRemainingTime,
        notes: optionalText(changePlanForm.notes),
      }

      const response = await changeBusinessPlan(business.id, payload)

      await refreshAfterOperation(response.message)
      setChangePlanForm((currentForm) => ({
        ...currentForm,
        notes: "",
      }))
    } catch (error) {
      setOperationErrorMessage(getErrorMessage(error))
    } finally {
      setSavingMode(null)
    }
  }

  async function handleStatusUpdate(targetStatus: SubscriptionStatus) {
    if (currentSubscription?.status === targetStatus) {
      setOperationErrorMessage("İşletme zaten seçilen durumda.")
      return
    }

    setSavingMode("status")
    setOperationErrorMessage(null)
    setSuccessMessage(null)

    try {
      const response = await updateBusinessSubscriptionStatus(business.id, {
        status: targetStatus,
        notes: optionalText(statusForm.notes),
      })

      await refreshAfterOperation(response.message)
      setStatusForm(initialStatusFormState)
    } catch (error) {
      setOperationErrorMessage(getErrorMessage(error))
    } finally {
      setSavingMode(null)
    }
  }

  return (
    <section className="flex flex-col gap-4">
      <div className="rounded-[1.7rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-sm">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <p className="text-[0.68rem] font-black uppercase tracking-[0.18em] text-[var(--missio-text-muted)]">
              Müşteri erişimi
            </p>
            <h2 className="mt-1 text-xl font-black text-[var(--missio-text-main)]">
              Abonelik durumu
            </h2>
            <p className="mt-2 text-sm font-bold leading-6 text-[var(--missio-text-muted)]">
              {business.name} için deneme süresini, paketini ve sisteme giriş durumunu yönet.
            </p>
          </div>

          <button
            type="button"
            onClick={() => void loadOverview(false)}
            disabled={isLoading}
            className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-cyan-100 text-cyan-700 disabled:opacity-60 dark:bg-cyan-950 dark:text-cyan-200"
            aria-label="Abonelik bilgilerini yenile"
          >
            <RefreshCw size={22} className={isLoading ? "animate-spin" : ""} />
          </button>
        </div>

        {loadErrorMessage && (
          <MessageBox type="error">{loadErrorMessage}</MessageBox>
        )}

        {isLoading && !overview ? (
          <div className="rounded-2xl bg-[var(--missio-soft-bg)] p-4 text-sm font-bold text-[var(--missio-text-muted)]">
            Abonelik bilgileri yükleniyor...
          </div>
        ) : overview ? (
          <>
            <div className="grid grid-cols-2 gap-2">
              <InfoCard
                label="Paket"
                value={currentPlan?.name ?? "Paket yok"}
                helper={getStatusLabel(currentSubscription?.status)}
              />
              <InfoCard
                label="Bitiş tarihi"
                value={formatDateTime(currentSubscription?.ends_at_utc ?? null)}
                helper={
                  overview.remaining_days === null
                    ? "Kalan gün yok"
                    : `${overview.remaining_days} gün kaldı`
                }
              />
              <InfoCard
                label="Aktif kullanıcı"
                value={`${overview.active_user_count} / ${
                  currentSubscription?.max_users_snapshot ?? "-"
                }`}
                helper="Paket limitine göre kontrol edilir."
              />
              <InfoCard
                label="Erişim"
                value={getAccessLabel(currentSubscription?.status, overview.is_expired)}
                helper={getAccessHelper(currentSubscription?.status, overview.is_expired)}
              />
            </div>

            <div className="mt-4 rounded-[1.45rem] border border-cyan-200 bg-cyan-50/70 p-3 dark:border-cyan-900 dark:bg-cyan-950/20">
              <div className="mb-3 flex items-center gap-2">
                <Sparkles size={18} className="text-cyan-700 dark:text-cyan-200" />
                <p className="text-sm font-black text-[var(--missio-text-main)]">
                  İşlem seç
                </p>
              </div>

              <div className="grid grid-cols-1 gap-2">
                <ActionButton
                  mode="extend"
                  activeMode={activeMode}
                  label={getExtendActionLabel(currentSubscription?.status)}
                  helper={
                    isTrialCustomer
                      ? "Deneme süresi mevcut bitiş tarihinden uzatılır."
                      : "Mevcut paketin bitiş tarihine süre eklenir."
                  }
                  icon={<CalendarDays size={18} />}
                  onClick={setActiveMode}
                />
                <ActionButton
                  mode="change-plan"
                  activeMode={activeMode}
                  label={getChangePlanActionLabel(currentSubscription?.status)}
                  helper={
                    isTrialCustomer
                      ? "Müşteri ücretli pakete geçirilir. Kalan süre korunur."
                      : "Yeni paket hemen aktif olur. Kalan süre korunur."
                  }
                  icon={<CreditCard size={18} />}
                  onClick={setActiveMode}
                />
                <ActionButton
                  mode="status"
                  activeMode={activeMode}
                  label={getStatusActionLabel(currentSubscription?.status)}
                  helper="Müşterinin sisteme giriş hakkını yönetir."
                  icon={<ShieldCheck size={18} />}
                  onClick={setActiveMode}
                />
              </div>
            </div>
          </>
        ) : null}
      </div>

      {overview && (
        <div className="rounded-[1.7rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-sm">
          {successMessage && (
            <div className="mb-4">
              <MessageBox type="success">
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={18} />
                  <p>{successMessage}</p>
                </div>
              </MessageBox>
            </div>
          )}

          {operationErrorMessage && (
            <div className="mb-4">
              <MessageBox type="error">
                <div className="flex items-start gap-2">
                  <AlertTriangle size={18} className="mt-0.5 shrink-0" />
                  <p>{operationErrorMessage}</p>
                </div>
              </MessageBox>
            </div>
          )}

          {activeMode === "extend" && (
            <form className="space-y-4" onSubmit={handleExtendSubmit}>
              <div>
                <p className="text-[0.68rem] font-black uppercase tracking-[0.18em] text-[var(--missio-text-muted)]">
                  Deneme / abonelik işlemi
                </p>
                <h3 className="mt-1 text-lg font-black text-[var(--missio-text-main)]">
                  {getExtendActionLabel(currentSubscription?.status)}
                </h3>
                <p className="mt-2 text-sm font-bold leading-6 text-[var(--missio-text-muted)]">
                  Bu işlem paketi değiştirmez. Mevcut paket korunur.
                </p>
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <label className="block">
                  <span className="mb-1 block text-xs font-black text-[var(--missio-text-muted)]">
                    Periyot
                  </span>
                  <select
                    className="w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-input-bg)] px-4 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none"
                    value={extendForm.billingPeriod}
                    onChange={(event) =>
                      handleBillingPeriodChange(event.target.value as BillingPeriod)
                    }
                    required
                  >
                    <option value="monthly">Aylık / 30 gün</option>
                    <option value="yearly">Yıllık / 365 gün</option>
                    <option value="trial">Deneme / 14 gün</option>
                    <option value="manual">Manuel</option>
                    <option value="custom">Özel</option>
                  </select>
                </label>

                <label className="block">
                  <span className="mb-1 block text-xs font-black text-[var(--missio-text-muted)]">
                    Süre
                  </span>
                  <div className="flex items-center gap-2 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-input-bg)] px-4 py-3">
                    <input
                      type="number"
                      min={1}
                      max={3650}
                      className="min-w-0 flex-1 bg-transparent text-sm font-bold text-[var(--missio-text-main)] outline-none"
                      value={extendForm.durationDays}
                      onChange={(event) =>
                        setExtendForm((currentForm) => ({
                          ...currentForm,
                          durationDays: event.target.value,
                        }))
                      }
                      required
                    />
                    <span className="text-xs font-black text-[var(--missio-text-muted)]">
                      gün
                    </span>
                  </div>
                </label>
              </div>

              <MessageBox type="info">
                <div className="flex items-start gap-2">
                  <Info size={18} className="mt-0.5 shrink-0" />
                  <div>
                    <p>Paket değişmeyecek: {currentPlan?.name ?? "Paket yok"}</p>
                    <p>
                      Tahmini yeni bitiş:{" "}
                      {estimatedExtendedEndDate
                        ? formatDateTime(estimatedExtendedEndDate.toISOString())
                        : "-"}
                    </p>
                  </div>
                </div>
              </MessageBox>

              <label className="block">
                <span className="mb-1 block text-xs font-black text-[var(--missio-text-muted)]">
                  Not
                </span>
                <textarea
                  className="min-h-24 w-full resize-none rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-input-bg)] px-4 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none"
                  value={extendForm.notes}
                  onChange={(event) =>
                    setExtendForm((currentForm) => ({
                      ...currentForm,
                      notes: event.target.value,
                    }))
                  }
                  placeholder="Örn: Müşterinin deneme süresi uzatıldı."
                  maxLength={1000}
                />
              </label>

              <button
                type="submit"
                disabled={savingMode !== null}
                className="flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 text-sm font-black text-white shadow-sm disabled:cursor-not-allowed disabled:opacity-60"
              >
                {savingMode === "extend" ? (
                  <Loader2 size={18} className="animate-spin" />
                ) : (
                  <CalendarDays size={18} />
                )}
                {savingMode === "extend" ? "Uzatılıyor" : getExtendActionLabel(currentSubscription?.status)}
              </button>
            </form>
          )}

          {activeMode === "change-plan" && (
            <form className="space-y-4" onSubmit={handleChangePlanSubmit}>
              <div>
                <p className="text-[0.68rem] font-black uppercase tracking-[0.18em] text-[var(--missio-text-muted)]">
                  Paket işlemi
                </p>
                <h3 className="mt-1 text-lg font-black text-[var(--missio-text-main)]">
                  {getChangePlanActionLabel(currentSubscription?.status)}
                </h3>
                <p className="mt-2 text-sm font-bold leading-6 text-[var(--missio-text-muted)]">
                  Paket hemen aktif olur. Varsayılan olarak mevcut bitiş tarihi korunur.
                </p>
              </div>

              <label className="block">
                <span className="mb-1 block text-xs font-black text-[var(--missio-text-muted)]">
                  Yeni paket
                </span>
                <select
                  className="w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-input-bg)] px-4 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none"
                  value={changePlanForm.planCode}
                  onChange={(event) =>
                    setChangePlanForm((currentForm) => ({
                      ...currentForm,
                      planCode: event.target.value,
                    }))
                  }
                  required
                >
                  {planOptions.map((plan) => (
                    <option key={plan.id} value={plan.code}>
                      {plan.name} — {plan.max_users} kullanıcı
                    </option>
                  ))}
                </select>
              </label>

              {selectedPlan && (
                <div className="rounded-[1.35rem] border border-[var(--missio-border)] bg-[var(--missio-soft-bg)] p-4">
                  <div className="mb-3 flex items-center gap-2">
                    {planDirection.icon}
                    <p className="text-sm font-black text-[var(--missio-text-main)]">
                      {planDirection.label}
                    </p>
                  </div>

                  <p className="mb-3 text-xs font-bold leading-5 text-[var(--missio-text-muted)]">
                    {planDirection.helper}
                  </p>

                  <div className="grid grid-cols-2 gap-2 text-xs font-bold text-[var(--missio-text-muted)]">
                    <p>Kullanıcı limiti: {selectedPlan.max_users}</p>
                    <p>Aktif kullanıcı: {overview.active_user_count}</p>
                    <p>Aylık: {formatMoney(selectedPlan.price_monthly, selectedPlan.currency)}</p>
                    <p>Yıllık: {formatMoney(selectedPlan.price_yearly, selectedPlan.currency)}</p>
                    <p>Günlük görev: {selectedPlan.max_daily_tasks ?? "Sınırsız"}</p>
                    <p>Rapor saklama: {selectedPlan.report_retention_days} gün</p>
                  </div>
                </div>
              )}

              {isDowngradeBlocked && (
                <MessageBox type="warning">
                  Seçilen paketin kullanıcı limiti mevcut aktif kullanıcı sayısından düşük.
                  Önce aktif kullanıcı sayısını azaltmalı veya daha yüksek paket seçmelisin.
                </MessageBox>
              )}

              <label className="flex items-start gap-3 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-soft-bg)] p-3">
                <input
                  type="checkbox"
                  checked={changePlanForm.preserveRemainingTime}
                  onChange={(event) =>
                    setChangePlanForm((currentForm) => ({
                      ...currentForm,
                      preserveRemainingTime: event.target.checked,
                    }))
                  }
                  className="mt-1"
                />
                <span>
                  <span className="block text-sm font-black text-[var(--missio-text-main)]">
                    Mevcut bitiş tarihini koru
                  </span>
                  <span className="mt-1 block text-xs font-bold leading-5 text-[var(--missio-text-muted)]">
                    Tavsiye edilen davranış budur. Paket değişir, kalan süre yanmaz.
                  </span>
                </span>
              </label>

              <label className="block">
                <span className="mb-1 block text-xs font-black text-[var(--missio-text-muted)]">
                  Not
                </span>
                <textarea
                  className="min-h-24 w-full resize-none rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-input-bg)] px-4 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none"
                  value={changePlanForm.notes}
                  onChange={(event) =>
                    setChangePlanForm((currentForm) => ({
                      ...currentForm,
                      notes: event.target.value,
                    }))
                  }
                  placeholder="Örn: Professional pakete geçirildi, kalan süre korundu."
                  maxLength={1000}
                />
              </label>

              <button
                type="submit"
                disabled={savingMode !== null || isDowngradeBlocked || isSamePlan}
                className="flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 text-sm font-black text-white shadow-sm disabled:cursor-not-allowed disabled:opacity-60"
              >
                {savingMode === "change-plan" ? (
                  <Loader2 size={18} className="animate-spin" />
                ) : (
                  <CreditCard size={18} />
                )}
                {savingMode === "change-plan" ? "Güncelleniyor" : getChangePlanActionLabel(currentSubscription?.status)}
              </button>
            </form>
          )}

          {activeMode === "status" && (
            <div className="space-y-4">
              <div>
                <p className="text-[0.68rem] font-black uppercase tracking-[0.18em] text-[var(--missio-text-muted)]">
                  Erişim işlemi
                </p>
                <h3 className="mt-1 text-lg font-black text-[var(--missio-text-main)]">
                  Müşteri erişimini yönet
                </h3>
                <p className="mt-2 text-sm font-bold leading-6 text-[var(--missio-text-muted)]">
                  Askıya alınan işletmede patron, yönetici ve personel sisteme giriş yapamaz.
                </p>
              </div>

              <MessageBox type="info">
                Mevcut durum: {getStatusLabel(currentSubscription?.status)}
              </MessageBox>

              <label className="block">
                <span className="mb-1 block text-xs font-black text-[var(--missio-text-muted)]">
                  Not
                </span>
                <textarea
                  className="min-h-24 w-full resize-none rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-input-bg)] px-4 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none"
                  value={statusForm.notes}
                  onChange={(event) =>
                    setStatusForm({
                      notes: event.target.value,
                    })
                  }
                  placeholder="Örn: Ödeme bekleniyor, abonelik askıya alındı."
                  maxLength={1000}
                />
              </label>

              <div className="grid grid-cols-1 gap-2">
                <button
                  type="button"
                  disabled={savingMode !== null || currentSubscription?.status === "suspended"}
                  onClick={() => void handleStatusUpdate("suspended")}
                  className="flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-amber-500 px-4 text-sm font-black text-white shadow-sm disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {savingMode === "status" ? (
                    <Loader2 size={18} className="animate-spin" />
                  ) : (
                    <PauseCircle size={18} />
                  )}
                  İşletmeyi askıya al
                </button>

                <button
                  type="button"
                  disabled={savingMode !== null || currentSubscription?.status === "active"}
                  onClick={() => void handleStatusUpdate("active")}
                  className="flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-emerald-600 px-4 text-sm font-black text-white shadow-sm disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {savingMode === "status" ? (
                    <Loader2 size={18} className="animate-spin" />
                  ) : (
                    <PlayCircle size={18} />
                  )}
                  Tekrar aktif et
                </button>
              </div>

              <MessageBox type="warning">
                İptal işlemini ayrı bir adım olarak ekleyeceğiz. Şu anda yanlışlıkla
                müşteri kapatmayı önlemek için bu ekrana alınmadı.
              </MessageBox>
            </div>
          )}
        </div>
      )}
    </section>
  )
}
