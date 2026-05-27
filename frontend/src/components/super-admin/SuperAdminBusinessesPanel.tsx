import { CreditCard } from "lucide-react"
import {
  ArrowLeft,
  BarChart3,
  Building2,
  CheckCircle2,
  ClipboardCheck,
  FileCheck2,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  UserPlus,
  UsersRound,
} from "lucide-react"
import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react"
import { useTranslation, type TranslationKey } from "../../i18n/language"

import { ApprovalsPanel } from "../approvals/ApprovalsPanel"
import { BossDashboardPanel } from "../boss/BossDashboardPanel"
import { BossReportsPanel } from "../boss/BossReportsPanel"
import { SuperAdminPlanPanel } from "./SuperAdminPlanPanel"
import { createBusinessWithOwner, listBusinesses } from "../../services/businessService"
import { ApiError } from "../../services/httpClient"
import type {
  BusinessResponse,
  BusinessWithOwnerCreatedResponse,
  CreateBusinessWithOwnerRequest,
} from "../../types/business"

type PanelMode = "list" | "create" | "manage"
type ManageTab = "summary" | "approvals" | "reports" | "plan"

type CreateBusinessFormState = {
  businessName: string
  businessSlug: string
  businessPhone: string
  businessEmail: string
  businessAddress: string
  ownerFullName: string
  ownerUsername: string
  ownerPassword: string
  ownerEmail: string
}

const initialFormState: CreateBusinessFormState = {
  businessName: "",
  businessSlug: "",
  businessPhone: "",
  businessEmail: "",
  businessAddress: "",
  ownerFullName: "",
  ownerUsername: "",
  ownerPassword: "",
  ownerEmail: "",
}

function normalizeSlug(value: string) {
  return value
    .trim()
    .toLocaleLowerCase("tr-TR")
    .replaceAll("ı", "i")
    .replaceAll("ğ", "g")
    .replaceAll("ü", "u")
    .replaceAll("ş", "s")
    .replaceAll("ö", "o")
    .replaceAll("ç", "c")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
}

function normalizeUsername(value: string) {
  return value.trim().toLocaleLowerCase("tr-TR")
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
    return "Tarih yok"
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


function getSubscriptionStatusLabel(
  value: string | null,
  t: (key: TranslationKey) => string,
) {
  const labels: Record<string, TranslationKey> = {
    trialing: "superAdmin.business.subscription.trialing",
    active: "superAdmin.business.subscription.active",
    suspended: "superAdmin.business.subscription.suspended",
    cancelled: "superAdmin.business.subscription.cancelled",
    expired: "superAdmin.business.subscription.expired",
  }

  if (!value) {
    return t("superAdmin.business.subscription.none")
  }

  const key = labels[value]

  return key ? t(key) : value
}

function getBusinessRemainingDaysLabel(
  business: BusinessResponse,
  t: (key: TranslationKey) => string,
) {
  if (typeof business.subscription_remaining_days === "number") {
    if (business.subscription_remaining_days < 0) {
      return t("superAdmin.business.remaining.expired")
    }

    if (business.subscription_remaining_days === 0) {
      return t("superAdmin.business.remaining.today")
    }

    return `${business.subscription_remaining_days} ${t("superAdmin.business.remaining.dayLeft")}`
  }

  if (!business.subscription_ends_at_utc) {
    return t("superAdmin.business.remaining.noEndDate")
  }

  const endDate = new Date(business.subscription_ends_at_utc)

  if (Number.isNaN(endDate.getTime())) {
    return t("superAdmin.business.remaining.badEndDate")
  }

  const now = new Date()
  const remainingDays = Math.ceil((endDate.getTime() - now.getTime()) / 86_400_000)

  if (remainingDays < 0) {
    return t("superAdmin.business.remaining.expired")
  }

  if (remainingDays === 0) {
    return t("superAdmin.business.remaining.today")
  }

  return `${remainingDays} ${t("superAdmin.business.remaining.dayLeft")}`
}

function buildPayload(formState: CreateBusinessFormState): CreateBusinessWithOwnerRequest {
  return {
    business_name: formState.businessName.trim(),
    business_slug: normalizeSlug(formState.businessSlug),
    business_phone: optionalText(formState.businessPhone),
    business_email: optionalText(formState.businessEmail)?.toLocaleLowerCase("tr-TR") ?? null,
    business_address: optionalText(formState.businessAddress),
    owner_full_name: formState.ownerFullName.trim(),
    owner_username: normalizeUsername(formState.ownerUsername),
    owner_password: formState.ownerPassword.trim(),
    owner_email: optionalText(formState.ownerEmail)?.toLocaleLowerCase("tr-TR") ?? null,
    owner_role: "boss",
    timezone: "Asia/Nicosia",
    default_theme: "dark",
  }
}

function MetricCard({
  label,
  value,
  helper,
  icon,
}: {
  label: string
  value: string | number
  helper: string
  icon: ReactNode
}) {
  return (
    <div className="rounded-[1.35rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
      <div className="mb-2 flex items-center justify-between gap-2">
        <p className="text-[0.66rem] font-black uppercase tracking-[0.15em] text-[var(--missio-text-muted)]">
          {label}
        </p>
        <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200">
          {icon}
        </div>
      </div>
      <p className="text-2xl font-black text-[var(--missio-text-main)]">{value}</p>
      <p className="mt-1 text-xs font-bold leading-5 text-[var(--missio-text-muted)]">
        {helper}
      </p>
    </div>
  )
}

function CreatedResultBanner({
  result,
  onManage,
}: {
  result: BusinessWithOwnerCreatedResponse
  onManage: (business: BusinessResponse) => void
}) {
  return (
    <div className="rounded-[1.5rem] border border-emerald-200 bg-emerald-50 p-4 shadow-sm dark:border-emerald-900 dark:bg-emerald-950/40">
      <div className="mb-3 flex items-center gap-2 text-emerald-700 dark:text-emerald-200">
        <CheckCircle2 size={20} />
        <p className="text-sm font-black">İşletme başarıyla oluşturuldu</p>
      </div>

      <div className="space-y-1 text-sm font-bold text-[var(--missio-text-main)]">
        <p>
          İşletme: <span className="font-black">{result.business.name}</span>
        </p>
        <p>
          İşletme kodu: <span className="font-black">{result.business.slug}</span>
        </p>
        <p>
          Patron kullanıcı: <span className="font-black">{result.owner_user.username}</span>
        </p>
        <p>
          Abonelik:{" "}
          <span className="font-black">{result.subscription?.status ?? "abonelik yok"}</span>
        </p>
        <p>
          Kullanıcı limiti:{" "}
          <span className="font-black">
            {result.subscription?.max_users_snapshot ?? "-"}
          </span>
        </p>
      </div>

      <button
        type="button"
        onClick={() => onManage(result.business)}
        className="mt-3 flex min-h-11 w-full items-center justify-center gap-2 rounded-2xl bg-emerald-600 px-4 text-sm font-black text-white shadow-sm"
      >
        <ShieldCheck size={18} />
        Bu işletmeyi yönet
      </button>
    </div>
  )
}

function BusinessCard({
  business,
  onManage,
}: {
  business: BusinessResponse
  onManage: (business: BusinessResponse) => void
}) {
  const { t } = useTranslation()

  return (
    <div className="rounded-[1.35rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-base font-black text-[var(--missio-text-main)]">
            {business.name}
          </p>
          <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
            {t("superAdmin.business.code")}: {business.slug}
          </p>
          <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
            {t("superAdmin.business.createdAt")}: {formatDateTime(business.created_at)}
          </p>
        </div>

        <span
          className={
            business.is_active
              ? "shrink-0 rounded-full bg-emerald-100 px-3 py-1 text-[0.68rem] font-black text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200"
              : "shrink-0 rounded-full bg-rose-100 px-3 py-1 text-[0.68rem] font-black text-rose-700 dark:bg-rose-950 dark:text-rose-200"
          }
        >
          {business.is_active ? t("superAdmin.business.active") : t("superAdmin.business.passive")}
        </span>
      </div>

      <div className="mt-3 rounded-2xl border border-cyan-100 bg-cyan-50/70 p-3 text-xs font-bold leading-5 text-cyan-900 dark:border-cyan-900 dark:bg-cyan-950/20 dark:text-cyan-100">
        <div className="mb-2 flex items-center justify-between gap-2">
          <p className="font-black">
            {t("superAdmin.business.plan")}: {business.subscription_plan_name ?? t("superAdmin.business.noPlan")}
          </p>
          <span className="rounded-full bg-white px-2 py-1 text-[0.64rem] font-black text-cyan-700 shadow-sm dark:bg-slate-900 dark:text-cyan-200">
            {getSubscriptionStatusLabel(business.subscription_status, t)}
          </span>
        </div>

        <p>{t("superAdmin.business.endAt")}: {formatDateTime(business.subscription_ends_at_utc)}</p>
        <p>{t("superAdmin.business.remaining")}: {getBusinessRemainingDaysLabel(business, t)}</p>
        <p>{t("superAdmin.business.userLimit")}: {business.subscription_max_users ?? "-"}</p>
      </div>

      {(business.phone || business.email) && (
        <div className="mt-3 border-t border-[var(--missio-border)] pt-3 text-xs font-bold leading-5 text-[var(--missio-text-muted)]">
          {business.phone && <p>{t("superAdmin.business.phone")}: {business.phone}</p>}
          {business.email && <p>{t("superAdmin.business.email")}: {business.email}</p>}
        </div>
      )}

      <button
        type="button"
        onClick={() => onManage(business)}
        className="mt-3 flex min-h-11 w-full items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 text-sm font-black text-white shadow-sm"
      >
        <ShieldCheck size={18} />
        {t("superAdmin.business.manage")}
      </button>
    </div>
  )
}


function CreateBusinessPanel({
  onCancel,
  onCreated,
}: {
  onCancel: () => void
  onCreated: (result: BusinessWithOwnerCreatedResponse) => Promise<void>
}) {
  const [formState, setFormState] = useState<CreateBusinessFormState>(initialFormState)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const previewSlug = useMemo(() => {
    if (formState.businessSlug.trim()) {
      return normalizeSlug(formState.businessSlug)
    }

    return normalizeSlug(formState.businessName)
  }, [formState.businessName, formState.businessSlug])

  function updateField(field: keyof CreateBusinessFormState, value: string) {
    setFormState((currentFormState) => ({
      ...currentFormState,
      [field]: value,
    }))
  }

  function useBusinessNameAsSlug() {
    setFormState((currentFormState) => ({
      ...currentFormState,
      businessSlug: normalizeSlug(currentFormState.businessName),
    }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    setIsSubmitting(true)
    setErrorMessage(null)

    try {
      const payload = buildPayload({
        ...formState,
        businessSlug: formState.businessSlug || formState.businessName,
      })

      const response = await createBusinessWithOwner(payload)
      await onCreated(response)
    } catch (error) {
      setErrorMessage(getErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="flex flex-1 flex-col gap-4 pb-24">
      <div className="rounded-[1.7rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-sm">
        <button
          type="button"
          onClick={onCancel}
          className="mb-4 inline-flex items-center gap-2 rounded-2xl bg-[var(--missio-soft-bg)] px-3 py-2 text-xs font-black text-[var(--missio-text-main)]"
        >
          <ArrowLeft size={16} />
          İşletmelere dön
        </button>

        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[0.68rem] font-black uppercase tracking-[0.18em] text-[var(--missio-text-muted)]">
              Yeni müşteri
            </p>
            <h1 className="mt-1 text-2xl font-black text-[var(--missio-text-main)]">
              İşletme oluştur
            </h1>
            <p className="mt-2 text-sm font-bold leading-6 text-[var(--missio-text-muted)]">
              İşletme, ilk patron kullanıcısı ve deneme aboneliği tek işlemle açılır.
            </p>
          </div>

          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200">
            <Plus size={24} />
          </div>
        </div>
      </div>

      <form
        className="rounded-[1.7rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-sm"
        onSubmit={handleSubmit}
      >
        <div className="mb-4 flex items-center gap-2">
          <Sparkles size={18} className="text-cyan-500" />
          <h2 className="text-base font-black text-[var(--missio-text-main)]">
            İşletme bilgileri
          </h2>
        </div>

        <div className="space-y-3">
          <label className="block">
            <span className="mb-1 block text-xs font-black text-[var(--missio-text-muted)]">
              İşletme adı
            </span>
            <input
              className="w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-input-bg)] px-4 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none"
              value={formState.businessName}
              onChange={(event) => updateField("businessName", event.target.value)}
              placeholder="Örn: Ertan Market"
              required
              minLength={2}
              maxLength={200}
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-xs font-black text-[var(--missio-text-muted)]">
              İşletme kodu
            </span>
            <div className="flex gap-2">
              <input
                className="min-w-0 flex-1 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-input-bg)] px-4 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none"
                value={formState.businessSlug}
                onChange={(event) => updateField("businessSlug", event.target.value)}
                placeholder="örn: ertan-market"
                required
                minLength={3}
                maxLength={120}
              />
              <button
                type="button"
                className="rounded-2xl bg-[var(--missio-soft-bg)] px-3 text-xs font-black text-[var(--missio-text-main)]"
                onClick={useBusinessNameAsSlug}
              >
                Üret
              </button>
            </div>
            <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
              Önizleme: {previewSlug || "işletme-kodu"}
            </p>
          </label>

          <label className="block">
            <span className="mb-1 block text-xs font-black text-[var(--missio-text-muted)]">
              Telefon
            </span>
            <input
              className="w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-input-bg)] px-4 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none"
              value={formState.businessPhone}
              onChange={(event) => updateField("businessPhone", event.target.value)}
              placeholder="0533 846 31 31"
              maxLength={50}
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-xs font-black text-[var(--missio-text-muted)]">
              İşletme e-posta
            </span>
            <input
              className="w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-input-bg)] px-4 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none"
              value={formState.businessEmail}
              onChange={(event) => updateField("businessEmail", event.target.value)}
              placeholder="firma@example.com"
              maxLength={255}
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-xs font-black text-[var(--missio-text-muted)]">
              Adres
            </span>
            <textarea
              className="min-h-24 w-full resize-none rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-input-bg)] px-4 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none"
              value={formState.businessAddress}
              onChange={(event) => updateField("businessAddress", event.target.value)}
              placeholder="İşletme adresi"
              maxLength={500}
            />
          </label>
        </div>

        <div className="mb-4 mt-6 flex items-center gap-2">
          <UserPlus size={18} className="text-cyan-500" />
          <h2 className="text-base font-black text-[var(--missio-text-main)]">
            İlk patron kullanıcısı
          </h2>
        </div>

        <div className="space-y-3">
          <label className="block">
            <span className="mb-1 block text-xs font-black text-[var(--missio-text-muted)]">
              Patron adı soyadı
            </span>
            <input
              className="w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-input-bg)] px-4 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none"
              value={formState.ownerFullName}
              onChange={(event) => updateField("ownerFullName", event.target.value)}
              placeholder="Örn: Ahmet Yılmaz"
              required
              minLength={2}
              maxLength={200}
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-xs font-black text-[var(--missio-text-muted)]">
              Patron kullanıcı adı
            </span>
            <input
              className="w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-input-bg)] px-4 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none"
              value={formState.ownerUsername}
              onChange={(event) => updateField("ownerUsername", event.target.value)}
              placeholder="örn: ahmet"
              required
              minLength={3}
              maxLength={100}
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-xs font-black text-[var(--missio-text-muted)]">
              Geçici şifre
            </span>
            <input
              className="w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-input-bg)] px-4 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none"
              type="password"
              value={formState.ownerPassword}
              onChange={(event) => updateField("ownerPassword", event.target.value)}
              placeholder="Güçlü bir şifre gir"
              required
              minLength={1}
              maxLength={255}
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-xs font-black text-[var(--missio-text-muted)]">
              Patron e-posta
            </span>
            <input
              className="w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-input-bg)] px-4 py-3 text-sm font-bold text-[var(--missio-text-main)] outline-none"
              value={formState.ownerEmail}
              onChange={(event) => updateField("ownerEmail", event.target.value)}
              placeholder="patron@example.com"
              maxLength={255}
            />
          </label>
        </div>

        {errorMessage && (
          <div className="mt-5 rounded-[1.25rem] border border-rose-200 bg-rose-50 p-3 text-sm font-bold leading-6 text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-200">
            {errorMessage}
          </div>
        )}

        <div className="mt-5 flex gap-2">
          <button
            type="submit"
            disabled={isSubmitting}
            className="flex min-h-12 flex-1 items-center justify-center gap-2 rounded-2xl bg-cyan-500 px-4 text-sm font-black text-white shadow-sm disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? <Loader2 size={18} className="animate-spin" /> : <Building2 size={18} />}
            {isSubmitting ? "Oluşturuluyor" : "İşletme oluştur"}
          </button>

          <button
            type="button"
            className="min-h-12 rounded-2xl bg-[var(--missio-soft-bg)] px-4 text-sm font-black text-[var(--missio-text-main)]"
            onClick={onCancel}
            disabled={isSubmitting}
          >
            Vazgeç
          </button>
        </div>
      </form>
    </section>
  )
}

function BusinessManagePanel({
  business,
  activeTab,
  onTabChange,
  onBack,
}: {
  business: BusinessResponse
  activeTab: ManageTab
  onTabChange: (tab: ManageTab) => void
  onBack: () => void
}) {
  const { t } = useTranslation()

  const tabs: { id: ManageTab; label: string; icon: ReactNode }[] = [
    {
      id: "summary",
      label: "Özet",
      icon: <ClipboardCheck size={17} />,
    },
    {
      id: "approvals",
      label: "Onay",
      icon: <FileCheck2 size={17} />,
    },
    {
      id: "reports",
      label: "Rapor",
      icon: <BarChart3 size={17} />,
    },
    {
      id: "plan",
      label: "Plan",
      icon: <CreditCard size={17} />,
    },
  ]

  return (
    <section className="flex flex-1 flex-col gap-4 pb-24">
      <div className="rounded-[1.7rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-sm">
        <button
          type="button"
          onClick={onBack}
          className="mb-4 inline-flex items-center gap-2 rounded-2xl bg-[var(--missio-soft-bg)] px-3 py-2 text-xs font-black text-[var(--missio-text-main)]"
        >
          <ArrowLeft size={16} />
          İşletmelere dön
        </button>

        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-[0.68rem] font-black uppercase tracking-[0.18em] text-[var(--missio-text-muted)]">
              {t("superAdmin.business.hero.title")}
            </p>
            <h1 className="mt-1 truncate text-2xl font-black text-[var(--missio-text-main)]">
              {business.name}
            </h1>
            <p className="mt-1 text-sm font-bold text-[var(--missio-text-muted)]">
              {t("superAdmin.business.code")}: {business.slug}
            </p>
          </div>

          <span
            className={
              business.is_active
                ? "shrink-0 rounded-full bg-emerald-100 px-3 py-1 text-[0.68rem] font-black text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200"
                : "shrink-0 rounded-full bg-rose-100 px-3 py-1 text-[0.68rem] font-black text-rose-700 dark:bg-rose-950 dark:text-rose-200"
            }
          >
            {business.is_active ? t("superAdmin.business.active") : t("superAdmin.business.passive")}
          </span>
        </div>

        <div className="mt-5 rounded-[1.7rem] border-2 border-cyan-200 bg-cyan-50/70 p-3 shadow-inner dark:border-cyan-900 dark:bg-cyan-950/20">
          <div className="mb-3 flex items-center justify-between gap-2">
            <div>
              <p className="text-[0.66rem] font-black uppercase tracking-[0.18em] text-cyan-700 dark:text-cyan-200">
                İşlem alanı
              </p>
              <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
                Yönetmek istediğin bölümü seç
              </p>
            </div>

            <span className="shrink-0 rounded-full bg-white px-3 py-1 text-[0.66rem] font-black text-cyan-700 shadow-sm ring-1 ring-cyan-100 dark:bg-slate-900 dark:text-cyan-200 dark:ring-cyan-900">
              Seçili: {tabs.find((tab) => tab.id === activeTab)?.label ?? "Özet"}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => onTabChange(tab.id)}
                className={
                  activeTab === tab.id
                    ? "flex min-h-14 flex-col items-center justify-center gap-1.5 rounded-2xl bg-[var(--missio-primary)] px-2 text-xs font-black text-white shadow-lg shadow-teal-500/25 ring-2 ring-cyan-200 transition active:scale-95 dark:ring-cyan-900"
                    : "flex min-h-14 flex-col items-center justify-center gap-1.5 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-2 text-xs font-black text-[var(--missio-text-muted)] shadow-sm transition active:scale-95"
                }
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {activeTab === "summary" ? (
        <BossDashboardPanel
          businessId={business.id}
          onOpenApprovals={() => onTabChange("approvals")}
          onOpenReports={() => onTabChange("reports")}
        />
      ) : activeTab === "approvals" ? (
        <ApprovalsPanel
          businessId={business.id}
          onChanged={() => undefined}
        />
      ) : activeTab === "reports" ? (
        <BossReportsPanel businessId={business.id} />
      ) : (
        <SuperAdminPlanPanel business={business} />
      )}
    </section>
  )
}

export function SuperAdminBusinessesPanel() {
  const { t } = useTranslation()
  const [mode, setMode] = useState<PanelMode>("list")
  const [businesses, setBusinesses] = useState<BusinessResponse[]>([])
  const [selectedBusiness, setSelectedBusiness] = useState<BusinessResponse | null>(null)
  const [manageTab, setManageTab] = useState<ManageTab>("summary")
  const [searchValue, setSearchValue] = useState("")
  const [isLoadingBusinesses, setIsLoadingBusinesses] = useState(false)
  const [businessesErrorMessage, setBusinessesErrorMessage] = useState<string | null>(null)
  const [createdResult, setCreatedResult] = useState<BusinessWithOwnerCreatedResponse | null>(null)

  useEffect(() => {
    void loadBusinesses()
  }, [])

  const activeBusinessCount = businesses.filter((business) => business.is_active).length
  const passiveBusinessCount = businesses.length - activeBusinessCount

  const filteredBusinesses = useMemo(() => {
    const keyword = searchValue.trim().toLocaleLowerCase("tr-TR")

    if (!keyword) {
      return businesses
    }

    return businesses.filter((business) => {
      return (
        business.name.toLocaleLowerCase("tr-TR").includes(keyword) ||
        business.slug.toLocaleLowerCase("tr-TR").includes(keyword) ||
        (business.phone ?? "").toLocaleLowerCase("tr-TR").includes(keyword) ||
        (business.email ?? "").toLocaleLowerCase("tr-TR").includes(keyword)
      )
    })
  }, [businesses, searchValue])

  async function loadBusinesses() {
    setIsLoadingBusinesses(true)
    setBusinessesErrorMessage(null)

    try {
      const response = await listBusinesses()
      setBusinesses(response)
    } catch (error) {
      setBusinessesErrorMessage(getErrorMessage(error))
    } finally {
      setIsLoadingBusinesses(false)
    }
  }

  function openManageMode(business: BusinessResponse) {
    setSelectedBusiness(business)
    setManageTab("summary")
    setCreatedResult(null)
    setMode("manage")
  }

  async function handleBusinessCreated(result: BusinessWithOwnerCreatedResponse) {
    setCreatedResult(result)
    setSearchValue("")
    setMode("list")
    await loadBusinesses()
  }

  if (mode === "create") {
    return (
      <CreateBusinessPanel
        onCancel={() => setMode("list")}
        onCreated={handleBusinessCreated}
      />
    )
  }

  if (mode === "manage" && selectedBusiness) {
    return (
      <BusinessManagePanel
        business={selectedBusiness}
        activeTab={manageTab}
        onTabChange={setManageTab}
        onBack={() => setMode("list")}
      />
    )
  }

  return (
    <section className="flex flex-1 flex-col gap-4 pb-24">
      <div className="rounded-[1.7rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-sm">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <p className="text-[0.68rem] font-black uppercase tracking-[0.18em] text-[var(--missio-text-muted)]">
              {t("superAdmin.business.hero.eyebrow")}
            </p>
            <h1 className="mt-1 text-2xl font-black text-[var(--missio-text-main)]">
              {t("superAdmin.business.hero.title")}
            </h1>
            <p className="mt-2 text-sm font-bold leading-6 text-[var(--missio-text-muted)]">
              {t("superAdmin.business.hero.description")}
            </p>
          </div>

          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200">
            <ShieldCheck size={24} />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2">
          <MetricCard
            label={t("superAdmin.business.metric.total")}
            value={businesses.length}
            helper={t("superAdmin.business.metric.business")}
            icon={<Building2 size={19} />}
          />
          <MetricCard
            label={t("superAdmin.business.metric.active")}
            value={activeBusinessCount}
            helper={t("superAdmin.business.metric.inUse")}
            icon={<UsersRound size={19} />}
          />
          <MetricCard
            label={t("superAdmin.business.metric.passive")}
            value={passiveBusinessCount}
            helper={t("superAdmin.business.metric.closed")}
            icon={<ShieldCheck size={19} />}
          />
        </div>

        <button
          type="button"
          onClick={() => {
            setCreatedResult(null)
            setMode("create")
          }}
          className="mt-4 flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 text-sm font-black text-white shadow-sm"
        >
          <Plus size={18} />
          {t("superAdmin.business.createButton")}
        </button>
      </div>

      {createdResult && (
        <CreatedResultBanner
          result={createdResult}
          onManage={openManageMode}
        />
      )}

      <div className="rounded-[1.7rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-sm">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <p className="text-[0.68rem] font-black uppercase tracking-[0.18em] text-[var(--missio-text-muted)]">
              {t("superAdmin.business.section.eyebrow")}
            </p>
            <h2 className="mt-1 text-xl font-black text-[var(--missio-text-main)]">
              {t("superAdmin.business.section.title")}
            </h2>
            <p className="mt-1 text-sm font-bold leading-5 text-[var(--missio-text-muted)]">
              {filteredBusinesses.length} {filteredBusinesses.length === 1 ? t("superAdmin.business.listingSingular") : t("superAdmin.business.listingPlural")}
            </p>
          </div>

          <button
            type="button"
            onClick={() => void loadBusinesses()}
            disabled={isLoadingBusinesses}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-soft-bg)] text-[var(--missio-text-main)] disabled:opacity-60"
            aria-label={t("superAdmin.business.refreshAria")}
          >
            <RefreshCw size={18} className={isLoadingBusinesses ? "animate-spin" : ""} />
          </button>
        </div>

        <div className="mb-3 flex items-center gap-2 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-input-bg)] px-4 py-3">
          <Search size={18} className="text-[var(--missio-text-muted)]" />
          <input
            value={searchValue}
            onChange={(event) => setSearchValue(event.target.value)}
            className="min-w-0 flex-1 bg-transparent text-sm font-bold text-[var(--missio-text-main)] outline-none placeholder:text-[var(--missio-text-muted)]"
            placeholder={t("superAdmin.business.searchPlaceholder")}
          />
        </div>

        {businessesErrorMessage && (
          <div className="mb-3 rounded-2xl border border-rose-200 bg-rose-50 p-3 text-sm font-bold leading-6 text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-200">
            {businessesErrorMessage}
          </div>
        )}

        {isLoadingBusinesses && businesses.length === 0 ? (
          <div className="rounded-2xl bg-[var(--missio-soft-bg)] p-4 text-sm font-bold text-[var(--missio-text-muted)]">
            {t("superAdmin.business.loading")}
          </div>
        ) : filteredBusinesses.length === 0 ? (
          <div className="rounded-2xl bg-[var(--missio-soft-bg)] p-4 text-sm font-bold text-[var(--missio-text-muted)]">
            {t("superAdmin.business.empty")}
          </div>
        ) : (
          <div className="space-y-3">
            {filteredBusinesses.map((business) => (
              <BusinessCard
                key={business.id}
                business={business}
                onManage={openManageMode}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
