import { Building2, CheckCircle2, Loader2, ShieldCheck, Sparkles, UserPlus } from "lucide-react"
import { useMemo, useState, type FormEvent } from "react"

import { createBusinessWithOwner } from "../../services/businessService"
import { ApiError } from "../../services/httpClient"
import type {
  BusinessWithOwnerCreatedResponse,
  CreateBusinessWithOwnerRequest,
} from "../../types/business"

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
    const detail = error.data as { detail?: unknown } | null

    if (typeof detail?.detail === "object" && detail.detail !== null) {
      const nestedDetail = detail.detail as { message?: unknown; errors?: unknown }

      if (typeof nestedDetail.message === "string") {
        if (Array.isArray(nestedDetail.errors) && nestedDetail.errors.length > 0) {
          return `${nestedDetail.message} ${nestedDetail.errors.join(" ")}`
        }

        return nestedDetail.message
      }
    }

    return error.message
  }

  if (error instanceof Error) {
    return error.message
  }

  return "İşletme oluşturulamadı."
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "Süre bilgisi yok"
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return "Süre bilgisi yok"
  }

  return date.toLocaleString("tr-TR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
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
    timezone: "Europe/Istanbul",
    default_theme: "dark",
  }
}

function ResultCard({ result }: { result: BusinessWithOwnerCreatedResponse }) {
  return (
    <div className="rounded-[1.5rem] border border-emerald-200 bg-emerald-50 p-4 shadow-sm dark:border-emerald-900 dark:bg-emerald-950/40">
      <div className="mb-3 flex items-center gap-2 text-emerald-700 dark:text-emerald-200">
        <CheckCircle2 size={20} />
        <p className="text-sm font-black">İşletme başarıyla oluşturuldu</p>
      </div>

      <div className="space-y-2 text-sm font-bold text-[var(--missio-text-main)]">
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
          <span className="font-black">
            {result.subscription?.status ?? "abonelik yok"}
          </span>
        </p>
        <p>
          Kullanıcı limiti:{" "}
          <span className="font-black">
            {result.subscription?.max_users_snapshot ?? "-"}
          </span>
        </p>
        <p>
          Deneme bitişi:{" "}
          <span className="font-black">
            {formatDateTime(result.subscription?.ends_at_utc ?? null)}
          </span>
        </p>
      </div>

      <p className="mt-3 rounded-2xl bg-white/70 p-3 text-xs font-bold leading-5 text-emerald-800 dark:bg-black/20 dark:text-emerald-100">
        Müşteri giriş yaparken işletme kodu, patron kullanıcı adı ve belirlediğiniz şifreyi
        kullanacak.
      </p>
    </div>
  )
}

export function SuperAdminBusinessesPanel() {
  const [formState, setFormState] = useState<CreateBusinessFormState>(initialFormState)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [createdResult, setCreatedResult] = useState<BusinessWithOwnerCreatedResponse | null>(null)

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

  function resetForm() {
    setFormState(initialFormState)
    setErrorMessage(null)
    setCreatedResult(null)
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    setIsSubmitting(true)
    setErrorMessage(null)
    setCreatedResult(null)

    try {
      const payload = buildPayload({
        ...formState,
        businessSlug: formState.businessSlug || formState.businessName,
      })

      const response = await createBusinessWithOwner(payload)
      setCreatedResult(response)
      setFormState(initialFormState)
    } catch (error) {
      setErrorMessage(getErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="flex flex-1 flex-col gap-4 pb-24">
      <div className="rounded-[1.7rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-sm">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <p className="text-[0.68rem] font-black uppercase tracking-[0.18em] text-[var(--missio-text-muted)]">
              Super Admin
            </p>
            <h1 className="mt-1 text-2xl font-black text-[var(--missio-text-main)]">
              Yeni işletme oluştur
            </h1>
            <p className="mt-2 text-sm font-bold leading-6 text-[var(--missio-text-muted)]">
              İşletmeyi, ilk patron kullanıcısını ve 14 günlük deneme aboneliğini tek
              işlemle oluştur.
            </p>
          </div>

          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200">
            <ShieldCheck size={24} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-2xl bg-[var(--missio-soft-bg)] p-3">
            <div className="mb-1 flex items-center gap-2 text-[var(--missio-text-muted)]">
              <Building2 size={16} />
              <p className="text-[0.68rem] font-black uppercase tracking-[0.14em]">
                İşletme
              </p>
            </div>
            <p className="text-sm font-black text-[var(--missio-text-main)]">
              Firma + kod
            </p>
          </div>

          <div className="rounded-2xl bg-[var(--missio-soft-bg)] p-3">
            <div className="mb-1 flex items-center gap-2 text-[var(--missio-text-muted)]">
              <UserPlus size={16} />
              <p className="text-[0.68rem] font-black uppercase tracking-[0.14em]">
                Patron
              </p>
            </div>
            <p className="text-sm font-black text-[var(--missio-text-main)]">
              İlk boss hesabı
            </p>
          </div>
        </div>
      </div>

      {createdResult && <ResultCard result={createdResult} />}

      {errorMessage && (
        <div className="rounded-[1.25rem] border border-rose-200 bg-rose-50 p-3 text-sm font-bold leading-6 text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-200">
          {errorMessage}
        </div>
      )}

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
            onClick={resetForm}
            disabled={isSubmitting}
          >
            Temizle
          </button>
        </div>
      </form>
    </section>
  )
}
